# app/api/api_v1/routes/websocket.py
import json
import logging
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pydantic import ValidationError

from app.api.deps import get_async_db, get_message_service
from app.schemas.message import MessageCreate
from app.sockets.manager import manager

router = APIRouter()
logger = logging.getLogger(__name__)


@router.websocket("/open")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()

    user_id: str | None = None

    try:
        # Handle initial connection
        user_id = await _handle_initial_connection(websocket)
        if not user_id:
            return

        # Connect to manager
        await manager.connect(websocket, user_id)
        await websocket.send_json({"msg": "connected", "user_id": user_id})

        # Main message loop
        await _handle_message_loop(websocket, user_id)

    except WebSocketDisconnect:
        logger.info(f"Client {user_id} disconnected")
    except Exception as e:
        logger.error(f"Unexpected error in WebSocket for user {user_id}: {e}")
        await _send_error(websocket, "Internal server error")
    finally:
        if user_id is not None:
            manager.disconnect(user_id)


async def _handle_initial_connection(websocket: WebSocket) -> str | None:
    """Handle initial connection and user authentication"""
    try:
        initial_data = await websocket.receive_text()
        initial_message = json.loads(initial_data)

        if initial_message.get("msg") != "connect" or "user_id" not in initial_message:
            await _send_error(websocket, "Invalid connection message")
            await websocket.close()
            return None

        return initial_message["user_id"]

    except json.JSONDecodeError:
        await _send_error(websocket, "Invalid JSON format")
        await websocket.close()
        return None
    except Exception as e:
        logger.error(f"Error in initial connection: {e}")
        await websocket.close()
        return None


async def _handle_message_loop(websocket: WebSocket, user_id: str):
    """Main message handling loop"""
    while True:
        message_data = await manager.get_message(user_id, timeout=30.0)

        if message_data is None:
            # Timeout -> send ping to keep connection alive
            await manager.ping(user_id)
            continue

        try:
            message = json.loads(message_data)
            await _process_message(websocket, user_id, message)

        except json.JSONDecodeError:
            await _send_error(websocket, "Invalid JSON format")
            continue
        except Exception as e:
            logger.error(f"Error processing message for user {user_id}: {e}")
            await _send_error(websocket, "Failed to process message")
            continue


async def _process_message(websocket: WebSocket, user_id: str, message: dict[str, Any]):
    """Process different message types"""
    msg_type = message.get("msg")

    if msg_type == "ping":
        await websocket.send_json({"msg": "pong"})

    elif msg_type == "pong":
        # Log or ignore pong responses
        logger.debug(f"Received pong from user {user_id}")

    elif msg_type == "method" and message.get("method") == "send_message":
        await _handle_send_message(websocket, user_id, message)

    else:
        # Echo unknown messages (for debugging/testing)
        await websocket.send_json({"msg": "echo", "data": message})


async def _handle_send_message(
    websocket: WebSocket, user_id: str, message: dict[str, Any]
):
    """Handle incoming send_message requests"""
    try:
        # Get database session and message service
        async with get_async_db() as db_session:
            message_service = get_message_service(db_session)

            # Extract message data and validate
            message_payload = message.get("data", {})

            # Ensure sender_id matches the authenticated user
            message_payload["sender_id"] = user_id

            # Validate message data using Pydantic schema
            try:
                message_create = MessageCreate(**message_payload)
            except ValidationError as e:
                await _send_error(websocket, f"Invalid message format: {str(e)}")
                return

            # Send message using service
            saved_message, delivered = await message_service.send_message(
                message_create
            )

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

    except Exception as e:
        logger.error(f"Error handling send_message for user {user_id}: {e}")
        await _send_error(websocket, "Failed to send message")


async def _send_error(websocket: WebSocket, error_message: str):
    """Send error message to client"""
    try:
        await websocket.send_json({"msg": "error", "details": error_message})
    except Exception as e:
        logger.error(f"Failed to send error message: {e}")
