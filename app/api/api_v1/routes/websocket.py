# app/api/api_v1/routes/websocket.py
import asyncio
import json
import logging
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pydantic import ValidationError

from app.api.deps import MessageServiceDep
from app.schemas.message import MessageCreate
from app.services.message import MessageService
from app.sockets.manager import manager

router = APIRouter()
logger = logging.getLogger(__name__)


@router.websocket("/open")
async def websocket_endpoint(websocket: WebSocket, message_service: MessageServiceDep):
    await websocket.accept()
    logger.info("WebSocket connection accepted")

    user_id: str | None = None

    try:
        # Handle initial connection
        user_id = await _handle_initial_connection(websocket)
        if not user_id:
            logger.warning("Failed to establish initial connection")
            return

        logger.info(f"User {user_id} attempting to connect")

        # # Connect to manager
        await manager.connect(websocket, user_id)
        await websocket.send_json({"msg": "connected", "user_id": user_id})

        logger.info(f"User {user_id} successfully connected")

        # Main message loop
        await _handle_message_loop(websocket, user_id, message_service)

    except WebSocketDisconnect as e:
        logger.info(f"Client {user_id} disconnected normally: {e.code}")
    except ConnectionResetError:
        logger.info(f"Client {user_id} connection reset")
    except Exception as e:
        logger.error(f"Unexpected error in WebSocket for user {user_id}: {e}")
        try:
            await _send_error(websocket, "Internal server error")
        except Exception:
            logger.error(
                'Failed to send error message: Cannot call "send" once a close message has been sent.'
            )
    finally:
        if user_id is not None:
            logger.info(f"Cleaning up connection for user {user_id}")
            await manager.disconnect_async(user_id)  # Use async version
        logger.info("WebSocket connection fully closed")


async def _handle_initial_connection(websocket: WebSocket) -> str | None:
    """Handle initial connection and user authentication"""
    try:
        # Set a timeout for initial connection
        initial_data = await asyncio.wait_for(websocket.receive_text(), timeout=10.0)
        initial_message = json.loads(initial_data)

        if initial_message.get("msg") != "connect" or "user_id" not in initial_message:
            await _send_error(websocket, "Invalid connection message")
            await _safe_close(websocket)
            return None

        user_id = initial_message["user_id"]
        logger.info(f"Initial connection from user: {user_id}")
        return user_id

    except asyncio.TimeoutError:
        logger.warning("Timeout waiting for initial connection message")
        await _safe_close(websocket)
        return None
    except json.JSONDecodeError:
        logger.warning("Invalid JSON in initial connection")
        await _send_error(websocket, "Invalid JSON format")
        await _safe_close(websocket)
        return None
    except Exception as e:
        logger.error(f"Error in initial connection: {e}")
        await _safe_close(websocket)
        return None


async def _handle_message_loop(
    websocket: WebSocket, user_id: str, message_service: MessageService
):
    """Main message handling loop"""
    try:
        while True:
            message_data = await manager.get_message(user_id, timeout=30.0)

            if message_data is None:
                # Timeout -> send ping to keep connection alive
                ping_sent = await manager.ping(user_id)
                if not ping_sent:
                    logger.warning(
                        f"Failed to send ping to {user_id}, connection may be dead"
                    )
                    break
                continue

            try:
                message = json.loads(message_data)
                await _process_message(websocket, user_id, message, message_service)

            except json.JSONDecodeError:
                await _send_error(websocket, "Invalid JSON format")
                continue
            except Exception as e:
                logger.error(f"Error processing message for user {user_id}: {e}")
                await _send_error(websocket, "Failed to process message")
                continue

    except Exception as e:
        logger.error(f"Message loop error for user {user_id}: {e}")
        raise


async def _process_message(
    websocket: WebSocket,
    user_id: str,
    message: dict[str, Any],
    message_service: MessageService,
):
    """Process different message types"""
    msg_type = message.get("msg")
    logger.debug(f"Processing message type '{msg_type}' from user {user_id}")

    if msg_type == "ping":
        await websocket.send_json({"msg": "pong"})

    elif msg_type == "pong":
        # Log or ignore pong responses
        logger.debug(f"Received pong from user {user_id}")

    elif msg_type == "send_message":  # Updated to match client
        await _handle_send_message(websocket, user_id, message, message_service)

    elif msg_type == "get_conversations":
        await _handle_get_conversations(websocket, user_id, message_service)

    elif msg_type == "get_messages":
        await _handle_get_messages(websocket, user_id, message)

    else:
        # Echo unknown messages (for debugging/testing)
        logger.warning(f"Unknown message type '{msg_type}' from user {user_id}")
        await websocket.send_json({"msg": "echo", "data": message})


async def _handle_send_message(
    websocket: WebSocket,
    user_id: str,
    message: dict[str, Any],
    message_service: MessageService,
):
    """Handle incoming send_message requests"""
    # try:

    # Create message payload from the message data directly
    message_payload = {
        "sender_id": user_id,  # Override with authenticated user
        "recipient_id": message.get("recipient_id"),
        "content": message.get("content"),
        "content_type": message.get("content_type", "text"),
        "custom_metadata": message.get("custom_metadata", {}),
    }

    # Validate message data using Pydantic schema
    try:
        message_create = MessageCreate(**message_payload)
    except ValidationError as e:
        await _send_error(websocket, f"Invalid message format: {str(e)}")
        return

    # Send message using service
    saved_message, delivered = await message_service.send_message(message_create)

    # Send confirmation to sender
    await websocket.send_json(
        {
            "msg": "message_sent",
            "data": {
                "message_id": str(saved_message.id),
                "delivered": delivered,
                "created_at": saved_message.created_at.isoformat(),
            },
        }
    )

    logger.info(f"Message sent from {user_id} to {message.get('recipient_id')}")

    # except Exception as e:
    #     logger.error(f"Error handling send_message for user {user_id}: {e}")
    #     await _send_error(websocket, "Failed to send message")


async def _handle_get_conversations(
    websocket: WebSocket, user_id: str, message_service: MessageService
):
    """Handle get_conversations request"""
    try:
        conversations = await message_service.get_user_conversations(user_id)
        if not conversations:
            conversations = []
        await websocket.send_json(
            {
                "msg": "conversations",
                "conversations": conversations,
            }
        )
    except Exception as e:
        logger.error(f"Error getting conversations for user {user_id}: {e}")
        await _send_error(websocket, "Failed to get conversations")


async def _handle_get_messages(
    websocket: WebSocket, user_id: str, message: dict[str, Any]
):
    """Handle get_messages request"""
    try:
        recipient_id = message.get("recipient_id")
        message.get("limit", 50)

        # TODO: Implement message fetching logic
        await websocket.send_json(
            {
                "msg": "messages",
                "recipient_id": recipient_id,
                "messages": [],  # Placeholder
            }
        )
    except Exception as e:
        logger.error(f"Error getting messages for user {user_id}: {e}")
        await _send_error(websocket, "Failed to get messages")


async def _send_error(websocket: WebSocket, error_message: str):
    """Send error message to client"""
    try:
        await websocket.send_json({"msg": "error", "error": error_message})
    except Exception as e:
        logger.error(f"Failed to send error message: {e}")


async def _safe_close(websocket: WebSocket):
    """Safely close WebSocket connection"""
    try:
        await websocket.close()
    except Exception as e:
        logger.debug(f"Error closing websocket: {e}")
