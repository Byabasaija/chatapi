# app/sockets/socketio_server.py
import logging

import socketio
from fastapi import FastAPI

from app.api.deps import get_async_session
from app.schemas.message import MessageCreate
from app.services.message import MessageService

logger = logging.getLogger(__name__)

# Create Socket.IO server
sio = socketio.AsyncServer(
    cors_allowed_origins="*",  # Configure based on your CORS needs
    logger=True,
    engineio_logger=True,
)

# Store active connections: {user_id: session_id}
active_connections: dict[str, str] = {}

# Store session user mapping: {session_id: user_id}
session_users: dict[str, str] = {}


@sio.event
async def connect(sid: str, auth: dict = None):
    """Handle client connection"""
    logger.info(f"Client {sid} attempting to connect")

    # Get user_id from auth data
    if not auth or "user_id" not in auth:
        logger.warning(f"Client {sid} rejected: missing user_id in auth")
        await sio.disconnect(sid)
        return False

    user_id = auth["user_id"]

    # Handle existing connection from same user
    if user_id in active_connections:
        old_sid = active_connections[user_id]
        logger.info(f"User {user_id} reconnecting, disconnecting old session {old_sid}")
        await sio.disconnect(old_sid)
        # Clean up old session
        session_users.pop(old_sid, None)

    # Store connection mappings
    active_connections[user_id] = sid
    session_users[sid] = user_id

    logger.info(f"User {user_id} connected with session {sid}")

    # Send connection confirmation
    await sio.emit("connected", {"user_id": user_id}, room=sid)

    # Deliver any undelivered messages
    await deliver_undelivered_messages(user_id, sid)

    return True


@sio.event
async def disconnect(sid: str):
    """Handle client disconnection"""
    user_id = session_users.get(sid)
    if user_id:
        logger.info(f"User {user_id} disconnected (session {sid})")
        active_connections.pop(user_id, None)
        session_users.pop(sid, None)
    else:
        logger.info(f"Unknown session {sid} disconnected")


@sio.event
async def send_message(sid: str, data: dict):
    """Handle message sending"""
    user_id = session_users.get(sid)
    if not user_id:
        await sio.emit("error", {"message": "Not authenticated"}, room=sid)
        return

    try:
        # Get database session
        async with get_async_session() as db:
            message_service = MessageService(db)

            # Prepare message data
            message_data = {
                "sender_id": user_id,  # Use authenticated user ID
                "recipient_id": data.get("recipient_id"),
                "sender_name": data.get("sender_name"),
                "recipient_name": data.get("recipient_name"),
                "content": data.get("content"),
                "encrypted_payload": data.get("encrypted_payload"),
                "content_type": data.get("content_type", "text"),
                "custom_metadata": data.get("custom_metadata", {}),
            }

            # Validate and create message
            message_create = MessageCreate(**message_data)

            # Send message (save to DB and attempt delivery)
            saved_message, delivered = await message_service.send_message(
                message_create
            )

            # Send confirmation to sender
            await sio.emit(
                "message_sent",
                {
                    "message_id": str(saved_message.id),
                    "delivered": delivered,
                    "created_at": saved_message.created_at.isoformat(),
                },
                room=sid,
            )

            logger.info(
                f"Message sent from {user_id} to {data.get('recipient_id')}, delivered: {delivered}"
            )

    except Exception as e:
        logger.error(f"Error sending message from user {user_id}: {e}")
        await sio.emit("error", {"message": "Failed to send message"}, room=sid)


@sio.event
async def get_conversations(sid: str):
    """Handle get conversations request"""
    user_id = session_users.get(sid)
    if not user_id:
        await sio.emit("error", {"message": "Not authenticated"}, room=sid)
        return

    try:
        async with get_async_session() as db:
            message_service = MessageService(db)
            conversations = await message_service.get_user_conversations(user_id)

            await sio.emit(
                "conversations", {"conversations": conversations or []}, room=sid
            )

    except Exception as e:
        logger.error(f"Error getting conversations for user {user_id}: {e}")
        await sio.emit("error", {"message": "Failed to get conversations"}, room=sid)


@sio.event
async def get_messages(sid: str, data: dict):
    """Handle get messages request"""
    user_id = session_users.get(sid)
    if not user_id:
        await sio.emit("error", {"message": "Not authenticated"}, room=sid)
        return

    try:
        recipient_id = data.get("recipient_id")
        limit = data.get("limit", 50)

        if not recipient_id:
            await sio.emit("error", {"message": "recipient_id required"}, room=sid)
            return

        async with get_async_session() as db:
            message_service = MessageService(db)
            messages = await message_service.get_chat_history(
                sender_id=user_id, recipient_id=recipient_id, limit=limit
            )

            await sio.emit(
                "messages",
                {
                    "user_id": user_id,
                    "recipient_id": recipient_id,
                    "messages": messages or [],
                },
                room=sid,
            )

    except Exception as e:
        logger.error(f"Error getting messages for user {user_id}: {e}")
        await sio.emit("error", {"message": "Failed to get messages"}, room=sid)


@sio.event
async def ping(sid: str):
    """Handle ping for connection keepalive"""
    await sio.emit("pong", {}, room=sid)


async def deliver_undelivered_messages(user_id: str, sid: str):
    """Deliver undelivered messages when user comes online"""
    try:
        async with get_async_session() as db:
            message_service = MessageService(db)

            # Get undelivered messages for this user
            undelivered = await message_service.get_undelivered_messages(user_id)

            for message in undelivered:
                # Send message to user
                await sio.emit(
                    "message",
                    {
                        "message_id": str(message["id"]),
                        "content": message["content"],
                        "encrypted_payload": message["encrypted_payload"],
                        "content_type": message["content_type"],
                        "sender_id": message["sender_id"],
                        "sender_name": message["sender_name"],
                        "recipient_id": message["recipient_id"],
                        "recipient_name": message["recipient_name"],
                        "timestamp": message["created_at"],
                        "custom_metadata": message["custom_metadata"],
                    },
                    room=sid,
                )

                # Mark as delivered
                await message_service.mark_message_delivered(message["id"])

                # Send delivery confirmation to sender (if online)
                await send_delivery_confirmation(message)

            if undelivered:
                logger.info(
                    f"Delivered {len(undelivered)} undelivered messages to user {user_id}"
                )

    except Exception as e:
        logger.error(f"Error delivering undelivered messages to user {user_id}: {e}")


async def send_delivery_confirmation(message: dict):
    """Send delivery confirmation to message sender"""
    sender_id = message["sender_id"]
    sender_sid = active_connections.get(sender_id)

    if sender_sid:
        try:
            await sio.emit(
                "message_delivered",
                {
                    "message_id": str(message["id"]),
                    "recipient_id": message["recipient_id"],
                    "delivered_at": message.get("delivered_at"),
                },
                room=sender_sid,
            )
        except Exception as e:
            logger.error(f"Error sending delivery confirmation to {sender_id}: {e}")


def get_user_connection(user_id: str) -> str | None:
    """Get session ID for a connected user"""
    return active_connections.get(user_id)


def is_user_online(user_id: str) -> bool:
    """Check if user is currently online"""
    return user_id in active_connections


def get_online_users() -> list[str]:
    """Get list of online user IDs"""
    return list(active_connections.keys())


# FastAPI app integration
def mount_socketio(app: FastAPI):
    """Mount Socket.IO to FastAPI app"""
    socketio_app = socketio.ASGIApp(sio, app)
    return socketio_app
