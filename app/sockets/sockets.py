import logging

import socketio

from app.api.deps import get_async_db
from app.api.sockets_deps import inject_services
from app.schemas.message import MessageCreate
from app.services.client import ClientService
from app.services.message import MessageService

logger = logging.getLogger(__name__)

# Create Socket.IO server
sio_server = socketio.AsyncServer(
    cors_allowed_origins=[],
    logger=True,
    engineio_logger=True,
    async_mode="asgi",
)

sio_app = socketio.ASGIApp(socketio_server=sio_server, socketio_path="sockets")

# Store active connections: {user_id: session_id}
active_connections: dict[str, str] = {}

# Store session user mapping: {session_id: user_id}
session_users: dict[str, str] = {}


@sio_server.event
@inject_services(services=["client_service"])
async def connect(sid: str, environ: dict, auth: dict, client_service: ClientService):
    """Handle client connection with API key validation"""
    logger.info(f"Client {sid} attempting to connect {environ}")

    # Validate auth data
    if not auth or "user_id" not in auth or "api_key" not in auth:
        logger.warning(f"Client {sid} rejected: missing user_id or api_key in auth")
        await sio_server.disconnect(sid)
        return False

    user_id = auth["user_id"]

    # try:
    client = await client_service.verify_api_key(auth["api_key"])
    if not client:
        await sio_server.disconnect(sid)
        return False

    # Handle existing connection from same user within same client
    connection_key = f"{client.id}:{user_id}"  # Scope by client + user
    if connection_key in active_connections:
        old_sid = active_connections[connection_key]
        logger.info(
            f"User {user_id} from client {client.id} reconnecting, disconnecting old session {old_sid}"
        )
        await sio_server.disconnect(old_sid)

        # Remove old session from active connections
        active_connections.pop(user_id, None)

        # Clean up old session
        session_users.pop(old_sid, None)

    # Store connection mappings with client context
    active_connections[connection_key] = sid
    session_users[sid] = {
        "user_id": user_id,
        "client_id": str(client.id),
        "connection_key": connection_key,
    }

    logger.info(f"User {user_id} from client {client.id} connected with session {sid}")

    # Send connection confirmation
    await sio_server.emit(
        "connected", {"user_id": user_id, "client_id": str(client.id)}, room=sid
    )

    # Deliver any undelivered messages for this user within this client
    # await deliver_undelivered_messages(user_id, str(client.id), sid)

    return True

    # except Exception as e:
    #     logger.error(f"Error during connection for user {user_id}: {e}")
    #     await sio_server.disconnect(sid)
    #     return False


@sio_server.event
@inject_services(services=["message_service"])
async def get_conversations(
    sid: str,
    message_service: MessageService = None,
):
    user_info = session_users.get(sid)
    if user_info:
        user_id = user_info.get("user_id")

    if not user_id:
        await sio_server.emit("error", {"message": "Not authenticated"}, room=sid)
        return

    try:
        conversations = await message_service.get_user_conversations(user_id)
        await sio_server.emit(
            "conversations", {"conversations": conversations or []}, room=sid
        )

    except Exception as e:
        logger.error(f"Error getting conversations for user {user_id}: {e}")
        await sio_server.emit(
            "error", {"message": "Failed to get conversations"}, room=sid
        )


@sio_server.event
@inject_services(services=["message_service"])
async def send_message(
    sid: str,
    data: dict,
    message_service: MessageService = None,
):
    """Handle message sending"""
    user_info = session_users.get(sid)
    if user_info:
        user_id = user_info.get("user_id")

    if not user_id:
        await sio_server.emit("error", {"message": "Not authenticated"}, room=sid)
        return

    try:
        # Prepare message data (force sender_id from session context)
        message_data = {
            "sender_id": user_id,
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

        # Save + attempt delivery
        saved_message, delivered = await message_service.send_message(message_create)

        # Acknowledge to sender
        await sio_server.emit(
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
        await sio_server.emit("error", {"message": "Failed to send message"}, room=sid)


@sio_server.event
@inject_services(services=["message_service"])
async def get_messages(sid: str, data: dict, message_service: MessageService = None):
    """Handle get messages request"""
    user_info = session_users.get(sid)
    if user_info:
        user_id = user_info.get("user_id")

    if not user_id:
        await sio_server.emit("error", {"message": "Not authenticated"}, room=sid)
        return

    try:
        recipient_id = data.get("recipient_id")
        limit = data.get("limit", 50)

        if not recipient_id:
            await sio_server.emit(
                "error", {"message": "recipient_id required"}, room=sid
            )
            return

        messages = await message_service.get_chat_history(
            sender_id=user_id, recipient_id=recipient_id, limit=limit
        )

        await sio_server.emit(
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
        await sio_server.emit("error", {"message": "Failed to get messages"}, room=sid)


@sio_server.event
async def ping(sid: str):
    """Handle ping for connection keepalive"""
    await sio_server.emit("pong", {}, room=sid)


async def deliver_undelivered_messages(user_id: str, sid: str):
    """Deliver undelivered messages when user comes online"""
    try:
        async with get_async_db() as db:
            message_service = MessageService(db)

            # Get undelivered messages for this user
            undelivered = await message_service.get_undelivered_messages(user_id)

            for message in undelivered:
                # Send message to user
                await sio_server.emit(
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
            await sio_server.emit(
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
