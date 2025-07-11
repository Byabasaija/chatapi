# app/sockets/notification_utils.py
import logging
from typing import Any
from uuid import UUID

from app.schemas.notification import NotificationType
from app.sockets.sockets import get_room_members_online, sio_server

logger = logging.getLogger(__name__)


def check_room_has_online_users(room_id: UUID) -> bool:
    """
    Check if a room has any online users.

    Args:
        room_id: The room ID to check

    Returns:
        True if room has online users, False otherwise
    """
    try:
        online_members = get_room_members_online(str(room_id))
        return len(online_members) > 0
    except Exception as e:
        logger.error(f"Error checking online users for room {room_id}: {e}")
        return False


async def send_websocket_notification(
    content: str,
    subject: str | None = None,
    metadata: dict | None = None,
    room_id: UUID | None = None,
    notification_type: str = NotificationType.WEBSOCKET,
) -> dict[str, Any]:
    """
    Send a notification via WebSocket to a room.

    Args:
        content: The notification content/message
        subject: Optional notification subject/title
        metadata: Optional additional data to include
        room_id: Room ID to send to (required)
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

        # Determine target - only room-based notifications supported
        result = {
            "success": False,
            "delivered_to": [],
            "errors": [],
        }

        # Send to specified room
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
        else:
            error_msg = "room_id is required for WebSocket notifications"
            logger.error(error_msg)
            result["errors"].append(error_msg)
            result["success"] = False

        return result

    except Exception as e:
        error_msg = f"WebSocket notification error: {str(e)}"
        logger.error(error_msg)
        return {"success": False, "errors": [error_msg], "delivered_to": []}
