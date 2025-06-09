# app/sockets/manager.py
import asyncio
import logging
from typing import Any

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}
        self.message_queues: dict[str, asyncio.Queue] = {}
        self.receive_tasks: dict[str, asyncio.Task] = {}
        self._cleanup_lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket, user_id: str):
        """Connect a user to the WebSocket manager"""
        async with self._cleanup_lock:
            # Disconnect existing connection if any
            if user_id in self.active_connections:
                logger.info(
                    f"User {user_id} already connected, cleaning up old connection"
                )
                await self._cleanup_user_internal(user_id)

            self.active_connections[user_id] = websocket
            self.message_queues[user_id] = asyncio.Queue()
            self.receive_tasks[user_id] = asyncio.create_task(
                self._receive_loop(user_id, websocket)
            )

            logger.info(
                f"User {user_id} connected. Total connections: {len(self.active_connections)}"
            )

    def disconnect(self, user_id: str):
        """Disconnect a user from the WebSocket manager (sync version)"""
        if user_id in self.active_connections:
            asyncio.create_task(self.disconnect_async(user_id))

    async def disconnect_async(self, user_id: str):
        """Disconnect a user from the WebSocket manager (async version)"""
        async with self._cleanup_lock:
            await self._cleanup_user_internal(user_id)
        logger.info(
            f"User {user_id} disconnected. Total connections: {len(self.active_connections)}"
        )

    async def _cleanup_user_internal(self, user_id: str):
        """Internal cleanup method (must be called with lock held)"""
        # Cancel receive task
        if user_id in self.receive_tasks:
            task = self.receive_tasks[user_id]
            if not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
                except Exception as e:
                    logger.error(f"Error cancelling receive task for {user_id}: {e}")

        # Close WebSocket connection
        if user_id in self.active_connections:
            websocket = self.active_connections[user_id]
            try:
                if websocket.client_state.name != "DISCONNECTED":
                    await websocket.close()
            except Exception as e:
                logger.debug(f"Error closing websocket for {user_id}: {e}")

        # Clean up data structures
        self.active_connections.pop(user_id, None)
        self.message_queues.pop(user_id, None)
        self.receive_tasks.pop(user_id, None)

    async def _cleanup_user(self, user_id: str):
        """Clean up user's connection resources (with lock)"""
        async with self._cleanup_lock:
            await self._cleanup_user_internal(user_id)

    def get_ws(self, user_id: str) -> WebSocket | None:
        """Get WebSocket connection for a user"""
        return self.active_connections.get(user_id)

    def is_user_connected(self, user_id: str) -> bool:
        """Check if a user is currently connected"""
        return user_id in self.active_connections

    async def send_message(self, message_data: dict[str, Any]) -> bool:
        """
        Send a message to a recipient

        Args:
            message_data: Message data dictionary

        Returns:
            True if message was delivered, False otherwise
        """
        recipient_id = message_data.get("recipient_id")
        print(f"Sending message to recipient_id: {recipient_id}")
        if not recipient_id:
            logger.error("No recipient_id in message data")
            return False

        websocket = self.get_ws(user_id=recipient_id)
        if not websocket:
            logger.info(f"Recipient {recipient_id} not connected")
            return False

        # try:
        # Check if WebSocket is still connected
        if websocket.client_state.name == "DISCONNECTED":
            logger.info(f"WebSocket for {recipient_id} is disconnected")
            await self._cleanup_user(recipient_id)
            return False

        # Format message for recipient
        formatted_message = {
            "msg": "message",
            "message_id": str(message_data.get("id")),
            "content": message_data.get("content"),
            "content_type": message_data.get("content_type"),
            "sender_id": message_data.get("sender_id"),
            "recipient_id": message_data.get("recipient_id"),
            "sender_name": message_data.get("sender_name"),
            "recipient_name": message_data.get("recipient_name"),
            "timestamp": message_data.get("created_at"),  # Already a string
            "custom_metadata": message_data.get("custom_metadata"),
        }

        await websocket.send_json(formatted_message)
        logger.debug(f"Message sent to {recipient_id}")
        return True

        # except Exception as e:
        #     logger.error(f"Failed to send message to {recipient_id}: {e}")
        #     # Connection might be broken, clean up
        #     await self._cleanup_user(recipient_id)
        #     return False

    async def send_acknowledgment(self, data: dict[str, Any], sender_id: str) -> bool:
        """
        Send delivery acknowledgment to sender

        Args:
            data: Acknowledgment data
            sender_id: ID of the message sender

        Returns:
            True if acknowledgment was sent, False otherwise
        """
        websocket = self.get_ws(sender_id)
        if not websocket:
            logger.info(f"Sender {sender_id} not connected for acknowledgment")
            return False

        try:
            if websocket.client_state.name == "DISCONNECTED":
                await self._cleanup_user(sender_id)
                return False

            ack_message = {
                "msg": "delivered",
                "data": data,
            }
            await websocket.send_json(ack_message)
            logger.debug(f"Delivery acknowledgment sent to {sender_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to send acknowledgment to {sender_id}: {e}")
            await self._cleanup_user(sender_id)
            return False

    async def _receive_loop(self, user_id: str, websocket: WebSocket):
        """Receive messages from WebSocket and queue them"""
        logger.info(f"Starting receive loop for user {user_id}")
        try:
            while True:
                # Check if WebSocket is still connected
                if websocket.client_state.name == "DISCONNECTED":
                    logger.info(f"WebSocket disconnected for user {user_id}")
                    break

                try:
                    msg = await websocket.receive_text()
                    if user_id in self.message_queues:
                        await self.message_queues[user_id].put(msg)
                    else:
                        logger.warning(f"Message queue not found for user {user_id}")
                        break

                except Exception as e:
                    logger.info(f"Error receiving message for user {user_id}: {e}")
                    break

        except asyncio.CancelledError:
            logger.info(f"Receive loop cancelled for user {user_id}")
        except Exception as e:
            logger.error(f"Unexpected error in receive loop for user {user_id}: {e}")
        finally:
            logger.info(f"Receive loop ended for user {user_id}")
            # Don't auto-cleanup here as it might cause race conditions
            # Cleanup will be handled by the main WebSocket handler

    async def get_message(self, user_id: str, timeout: float = 30.0) -> str | None:
        """
        Get next message from user's queue

        Args:
            user_id: User ID
            timeout: Timeout in seconds

        Returns:
            Message string or None if timeout
        """
        queue = self.message_queues.get(user_id)
        if not queue:
            logger.warning(f"Message queue not found for user {user_id}")
            return None

        try:
            return await asyncio.wait_for(queue.get(), timeout=timeout)
        except asyncio.TimeoutError:
            return None
        except Exception as e:
            logger.error(f"Error getting message for user {user_id}: {e}")
            return None

    async def ping(self, user_id: str) -> bool:
        """
        Send ping to user to keep connection alive

        Args:
            user_id: User ID

        Returns:
            True if ping was sent, False otherwise
        """
        websocket = self.get_ws(user_id)
        if not websocket:
            return False

        try:
            if websocket.client_state.name == "DISCONNECTED":
                await self._cleanup_user(user_id)
                return False

            await websocket.send_json({"msg": "ping"})
            logger.debug(f"Ping sent to user {user_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to send ping to {user_id}: {e}")
            await self._cleanup_user(user_id)
            return False

    def get_connected_users(self) -> list[str]:
        """Get list of currently connected user IDs"""
        return list(self.active_connections.keys())

    def get_connection_count(self) -> int:
        """Get number of active connections"""
        return len(self.active_connections)

    async def broadcast_to_all(self, message: dict[str, Any], exclude_user: str = None):
        """Broadcast a message to all connected users"""
        disconnected_users = []

        for user_id, websocket in self.active_connections.items():
            if exclude_user and user_id == exclude_user:
                continue

            try:
                if websocket.client_state.name != "DISCONNECTED":
                    await websocket.send_json(message)
                else:
                    disconnected_users.append(user_id)
            except Exception as e:
                logger.error(f"Failed to broadcast to {user_id}: {e}")
                disconnected_users.append(user_id)

        # Clean up disconnected users
        for user_id in disconnected_users:
            await self._cleanup_user(user_id)


# Global manager instance
manager = ConnectionManager()
