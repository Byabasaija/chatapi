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

    async def connect(self, websocket: WebSocket, user_id: str):
        """Connect a user to the WebSocket manager"""
        # Disconnect existing connection if any
        if user_id in self.active_connections:
            await self._cleanup_user(user_id)

        self.active_connections[user_id] = websocket
        self.message_queues[user_id] = asyncio.Queue()
        self.receive_tasks[user_id] = asyncio.create_task(
            self._receive_loop(user_id, websocket)
        )
        logger.info(f"User {user_id} connected")

    def disconnect(self, user_id: str):
        """Disconnect a user from the WebSocket manager"""
        asyncio.create_task(self._cleanup_user(user_id))
        logger.info(f"User {user_id} disconnected")

    async def _cleanup_user(self, user_id: str):
        """Clean up user's connection resources"""
        if user_id in self.receive_tasks:
            self.receive_tasks[user_id].cancel()
            try:
                await self.receive_tasks[user_id]
            except asyncio.CancelledError:
                pass

        self.active_connections.pop(user_id, None)
        self.message_queues.pop(user_id, None)
        self.receive_tasks.pop(user_id, None)

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
        if not recipient_id:
            logger.error("No recipient_id in message data")
            return False

        websocket = self.get_ws(recipient_id)
        if not websocket:
            logger.info(f"Recipient {recipient_id} not connected")
            return False

        try:
            # Format message for recipient
            formatted_message = {
                "msg": "message",
                "data": {
                    "id": str(message_data.get("id")),
                    "content": message_data.get("content"),
                    "encrypted_payload": message_data.get("encrypted_payload"),
                    "content_type": message_data.get("content_type"),
                    "sender_id": message_data.get("sender_id"),
                    "recipient_id": message_data.get("recipient_id"),
                    "group_id": message_data.get("group_id"),
                    "custom_metadata": message_data.get("custom_metadata"),
                    "created_at": message_data.get("created_at").isoformat()
                    if message_data.get("created_at")
                    else None,
                },
            }

            await websocket.send_json(formatted_message)
            logger.debug(f"Message sent to {recipient_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to send message to {recipient_id}: {e}")
            # Connection might be broken, clean up
            await self._cleanup_user(recipient_id)
            return False

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
        try:
            while True:
                msg = await websocket.receive_text()
                if user_id in self.message_queues:
                    await self.message_queues[user_id].put(msg)

        except Exception as e:
            logger.info(f"Receive loop ended for user {user_id}: {e}")
        finally:
            # Clean up when receive loop ends
            await self._cleanup_user(user_id)

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
            return None

        try:
            return await asyncio.wait_for(queue.get(), timeout=timeout)
        except asyncio.TimeoutError:
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
            await websocket.send_json({"msg": "ping"})
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


# Global manager instance
manager = ConnectionManager()
