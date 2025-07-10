# app/sockets/notification_utils.py
import logging
from typing import Any
from uuid import UUID

from app.schemas.notification import NotificationType
from app.sockets.sockets import active_connections, sio_server

logger = logging.getLogger(__name__)


async def send_websocket_notification(
    content: str,
    subject: str | None = None,
    metadata: dict | None = None,
    room_id: UUID | None = None,
    target_client_id: UUID | None = None,
    notification_type: str = NotificationType.WEBSOCKET,
) -> dict[str, Any]:
    """
    Send a notification via WebSocket.

    Args:
        content: The notification content/message
        subject: Optional notification subject/title
        metadata: Optional additional data to include
        room_id: Optional room ID to send to
        target_client_id: Optional specific client ID to send to
        notification_type: The type of notification (default: websocket)

    Returns:
        Result of the WebSocket notification attempt
    """
    try:
        # Prepare notification payload
        notification_data = {
            "type": notification_type,
            "content": content,
            "timestamp": "",  # Will be filled by Socket.IO
        }

        # Add optional fields if provided
        if subject:
            notification_data["subject"] = subject

        if metadata:
            notification_data["metadata"] = metadata

        # Determine target(s)
        result = {
            "success": False,
            "delivered_to": [],
            "errors": [],
        }

        # Case 1: Send to a specific room
        if room_id:
            room_channel = f"room:{room_id}"
            logger.debug(f"Sending notification to room: {room_id}")
            try:
                await sio_server.emit(
                    "notification", notification_data, room=room_channel
                )
                result["success"] = True
                result["delivered_to"].append({"type": "room", "id": str(room_id)})
            except Exception as e:
                error_msg = f"Failed to send notification to room {room_id}: {str(e)}"
                logger.error(error_msg)
                result["errors"].append(error_msg)

        # Case 2: Send to a specific client
        elif target_client_id:
            client_id_str = str(target_client_id)
            # Find session ID for the client
            session_id = active_connections.get(client_id_str)

            if session_id:
                logger.debug(
                    f"Sending notification to client: {client_id_str} (session: {session_id})"
                )
                try:
                    await sio_server.emit(
                        "notification", notification_data, room=session_id
                    )
                    result["success"] = True
                    result["delivered_to"].append(
                        {"type": "client", "id": client_id_str}
                    )
                except Exception as e:
                    error_msg = f"Failed to send notification to client {client_id_str}: {str(e)}"
                    logger.error(error_msg)
                    result["errors"].append(error_msg)
            else:
                msg = f"Client {client_id_str} not connected"
                logger.warning(msg)
                result["errors"].append(msg)

        # Case 3: No valid target specified
        else:
            error_msg = "Either room_id or target_client_id must be specified"
            logger.error(error_msg)
            result["errors"].append(error_msg)
            result["success"] = False

        return result

    except Exception as e:
        error_msg = f"WebSocket notification error: {str(e)}"
        logger.error(error_msg)
        return {"success": False, "errors": [error_msg], "delivered_to": []}
