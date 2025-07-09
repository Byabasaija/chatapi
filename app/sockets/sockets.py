# app/sockets/sockets.py
import logging
from uuid import UUID

import socketio

from app.api.sockets_deps import inject_services
from app.schemas.message import MessageCreate
from app.services.client import ClientService
from app.services.message import MessageService
from app.services.room import RoomService

logger = logging.getLogger(__name__)

# Create Socket.IO server
sio_server = socketio.AsyncServer(
    cors_allowed_origins=[],
    logger=True,
    engineio_logger=True,
    async_mode="asgi",
)

sio_app = socketio.ASGIApp(socketio_server=sio_server, socketio_path="sockets")

# Store active connections: {connection_key: session_id}
active_connections: dict[str, str] = {}

# Store session user mapping: {session_id: user_info}
session_users: dict[str, dict] = {}

# Store user's joined rooms: {session_id: set[room_id]}
user_rooms: dict[str, set[str]] = {}


@sio_server.event
@inject_services(services=["client_service", "room_service"])
async def connect(
    sid: str,
    environ: dict,  # noqa
    auth: dict,
    client_service: ClientService,
    room_service: RoomService,
):
    """Handle client connection with API key validation"""
    logger.info(f"Client {sid} attempting to connect")

    # Validate auth data
    if not auth or "user_id" not in auth or "api_key" not in auth:
        logger.warning(f"Client {sid} rejected: missing user_id or api_key in auth")
        await sio_server.disconnect(sid)
        return False

    user_id = auth["user_id"]
    display_name = auth.get("display_name", user_id)

    # try:
    # Verify API key (master or scoped)
    client = await client_service.verify_master_api_key(auth["api_key"])
    scoped_key = None

    if not client:
        # Try scoped key
        result = await client_service.verify_scoped_api_key(auth["api_key"])
        if result:
            client, scoped_key = result
        else:
            await sio_server.disconnect(sid)
            return False

    # Use scoped key user_id if available
    if scoped_key:
        user_id = scoped_key.user_id
        display_name = scoped_key.user_id

    # Handle existing connection from same user within same client
    connection_key = f"{client.id}:{user_id}"  # Scope by client + user
    if connection_key in active_connections:
        old_sid = active_connections[connection_key]
        logger.info(
            f"User {user_id} from client {client.id} reconnecting, disconnecting old session {old_sid}"
        )
        await sio_server.disconnect(old_sid)

        # Clean up old session
        session_users.pop(old_sid, None)
        user_rooms.pop(old_sid, None)

    # Store connection mappings with client context
    active_connections[connection_key] = sid
    session_users[sid] = {
        "user_id": user_id,
        "display_name": display_name,
        "client_id": str(client.id),
        "connection_key": connection_key,
        "is_scoped": scoped_key is not None,
    }
    user_rooms[sid] = set()

    # Join user to their rooms
    await join_user_rooms(sid, user_id, client.id, room_service)
    await notify_user_online(user_id, client.id)

    logger.info(f"User {user_id} from client {client.id} connected with session {sid}")

    # Send connection confirmation
    await sio_server.emit(
        "connected",
        {
            "user_id": user_id,
            "client_id": str(client.id),
            "display_name": display_name,
        },
        room=sid,
    )

    return True

    # except Exception as e:
    #     logger.error(f"Error during connection for user {user_id}: {e}")
    #     await sio_server.disconnect(sid)
    #     return False


@sio_server.event
async def disconnect(sid: str):
    """Handle client disconnection"""
    user_info = session_users.get(sid)
    if user_info:
        connection_key = user_info.get("connection_key")
        user_id = user_info.get("user_id")
        client_id = user_info.get("client_id")

        # Leave all rooms
        if sid in user_rooms:
            for room_id in user_rooms[sid]:
                await sio_server.leave_room(sid, f"room:{room_id}")

        # Clean up mappings
        if connection_key:
            active_connections.pop(connection_key, None)
        session_users.pop(sid, None)
        user_rooms.pop(sid, None)

        if user_id:
            await notify_user_offline(user_id, client_id)

        logger.info(f"User {user_id} from client {client_id} disconnected")


# ==================== ROOM EVENTS ====================


@sio_server.event
@inject_services(services=["room_service"])
async def join_room(sid: str, data: dict, room_service: RoomService):
    """Join a specific room"""
    user_info = session_users.get(sid)
    if not user_info:
        await sio_server.emit("error", {"message": "Not authenticated"}, room=sid)
        return

    user_id = user_info.get("user_id")
    room_id = data.get("room_id")

    if not room_id:
        await sio_server.emit("error", {"message": "room_id required"}, room=sid)
        return

    try:
        # Check if user can access this room
        can_access = await room_service.user_can_access_room(UUID(room_id), user_id)
        if not can_access:
            await sio_server.emit(
                "error", {"message": "Access denied to room"}, room=sid
            )
            return

        # Join socket room
        await sio_server.enter_room(sid, f"room:{room_id}")
        user_rooms[sid].add(room_id)

        # Notify room members
        await sio_server.emit(
            "user_joined_room",
            {
                "user_id": user_id,
                "display_name": user_info.get("display_name"),
                "room_id": room_id,
            },
            room=f"room:{room_id}",
            skip_sid=sid,
        )

        await sio_server.emit("room_joined", {"room_id": room_id}, room=sid)
        logger.info(f"User {user_id} joined room {room_id}")

    except Exception as e:
        logger.error(f"Error joining room {room_id} for user {user_id}: {e}")
        await sio_server.emit("error", {"message": "Failed to join room"}, room=sid)


@sio_server.event
async def leave_room(sid: str, data: dict):
    """Leave a specific room"""
    user_info = session_users.get(sid)
    if not user_info:
        await sio_server.emit("error", {"message": "Not authenticated"}, room=sid)
        return

    user_id = user_info.get("user_id")
    room_id = data.get("room_id")

    if not room_id:
        await sio_server.emit("error", {"message": "room_id required"}, room=sid)
        return

    try:
        # Leave socket room
        await sio_server.leave_room(sid, f"room:{room_id}")
        if sid in user_rooms:
            user_rooms[sid].discard(room_id)

        # Notify room members
        await sio_server.emit(
            "user_left_room",
            {
                "user_id": user_id,
                "display_name": user_info.get("display_name"),
                "room_id": room_id,
            },
            room=f"room:{room_id}",
        )

        await sio_server.emit("room_left", {"room_id": room_id}, room=sid)
        logger.info(f"User {user_id} left room {room_id}")

    except Exception as e:
        logger.error(f"Error leaving room {room_id} for user {user_id}: {e}")
        await sio_server.emit("error", {"message": "Failed to leave room"}, room=sid)


@sio_server.event
@inject_services(services=["room_service"])
async def get_rooms(sid: str, room_service: RoomService):
    """Get user's rooms"""
    user_info = session_users.get(sid)
    if not user_info:
        await sio_server.emit("error", {"message": "Not authenticated"}, room=sid)
        return

    user_id = user_info.get("user_id")
    client_id = UUID(user_info.get("client_id"))

    try:
        rooms = await room_service.get_user_rooms(user_id, client_id)
        rooms_data = []
        for room in rooms:
            rooms_data.append(
                {
                    "room_id": str(room.id),
                    "name": room.name,
                    "description": room.description,
                    "room_type": room.room_type,
                    "member_count": len([m for m in room.memberships if m.is_active]),
                    "last_message_at": room.last_message_at.isoformat()
                    if room.last_message_at
                    else None,
                }
            )

        await sio_server.emit("rooms", {"rooms": rooms_data}, room=sid)

    except Exception as e:
        logger.error(f"Error getting rooms for user {user_id}: {e}")
        await sio_server.emit("error", {"message": "Failed to get rooms"}, room=sid)


# ==================== MESSAGE EVENTS ====================


@sio_server.event
@inject_services(services=["message_service", "room_service"])
async def send_message(
    sid: str,
    data: dict,
    message_service: MessageService,
    room_service: RoomService,
):
    """Handle message sending to a room"""
    user_info = session_users.get(sid)
    if not user_info:
        await sio_server.emit("error", {"message": "Not authenticated"}, room=sid)
        return

    user_id = user_info.get("user_id")
    display_name = user_info.get("display_name")
    room_id = data.get("room_id")

    if not room_id:
        await sio_server.emit("error", {"message": "room_id required"}, room=sid)
        return

    try:
        # Verify user can send messages to this room
        can_access = await room_service.user_can_access_room(UUID(room_id), user_id)
        if not can_access:
            await sio_server.emit(
                "error", {"message": "Access denied to room"}, room=sid
            )
            return

        # Prepare message data
        message_data = MessageCreate(
            room_id=UUID(room_id),
            sender_user_id=user_id,
            sender_display_name=display_name,
            content=data.get("content"),
            content_type=data.get("content_type", "text"),
            file_url=data.get("file_url"),
            file_name=data.get("file_name"),
            file_size=data.get("file_size"),
            file_mime_type=data.get("file_mime_type"),
            reply_to_id=UUID(data["reply_to_id"]) if data.get("reply_to_id") else None,
        )

        # Save message to database
        saved_message = await message_service.create_message(
            room_id=UUID(room_id),
            sender_user_id=user_id,
            sender_display_name=display_name,
            message_data=message_data,
        )

        # Format message for broadcast
        formatted_message = {
            "message_id": str(saved_message.id),
            "room_id": str(saved_message.room_id),
            "content": saved_message.content,
            "content_type": saved_message.content_type,
            "sender_user_id": saved_message.sender_user_id,
            "sender_display_name": saved_message.sender_display_name,
            "file_url": saved_message.file_url,
            "file_name": saved_message.file_name,
            "file_size": saved_message.file_size,
            "file_mime_type": saved_message.file_mime_type,
            "reply_to_id": str(saved_message.reply_to_id)
            if saved_message.reply_to_id
            else None,
            "is_edited": saved_message.is_edited,
            "created_at": saved_message.created_at.isoformat(),
        }

        # Broadcast to all room members
        await sio_server.emit("message", formatted_message, room=f"room:{room_id}")

        logger.info(f"Message sent from {user_id} to room {room_id}")

    except Exception as e:
        logger.error(f"Error sending message from user {user_id}: {e}")
        await sio_server.emit("error", {"message": "Failed to send message"}, room=sid)


@sio_server.event
@inject_services(services=["message_service", "room_service"])
async def get_messages(
    sid: str, data: dict, message_service: MessageService, room_service: RoomService
):
    """Handle get room messages request"""
    user_info = session_users.get(sid)
    if not user_info:
        await sio_server.emit("error", {"message": "Not authenticated"}, room=sid)
        return

    user_id = user_info.get("user_id")
    room_id = data.get("room_id")
    limit = data.get("limit", 50)
    offset = data.get("offset", 0)

    if not room_id:
        await sio_server.emit("error", {"message": "room_id required"}, room=sid)
        return

    try:
        # Verify access to room
        can_access = await room_service.user_can_access_room(UUID(room_id), user_id)
        if not can_access:
            await sio_server.emit(
                "error", {"message": "Access denied to room"}, room=sid
            )
            return

        messages = await message_service.get_room_messages(
            room_id=UUID(room_id), limit=limit, offset=offset
        )

        messages_data = []
        for msg in messages:
            messages_data.append(
                {
                    "message_id": str(msg.id),
                    "room_id": str(msg.room_id),
                    "content": msg.content,
                    "content_type": msg.content_type,
                    "sender_user_id": msg.sender_user_id,
                    "sender_display_name": msg.sender_display_name,
                    "file_url": msg.file_url,
                    "file_name": msg.file_name,
                    "file_size": msg.file_size,
                    "file_mime_type": msg.file_mime_type,
                    "reply_to_id": str(msg.reply_to_id) if msg.reply_to_id else None,
                    "is_edited": msg.is_edited,
                    "is_deleted": msg.is_deleted,
                    "created_at": msg.created_at.isoformat(),
                    "edited_at": msg.edited_at.isoformat() if msg.edited_at else None,
                }
            )

        await sio_server.emit(
            "messages",
            {
                "room_id": room_id,
                "messages": messages_data,
                "limit": limit,
                "offset": offset,
            },
            room=sid,
        )

    except Exception as e:
        logger.error(f"Error getting messages for room {room_id}: {e}")
        await sio_server.emit("error", {"message": "Failed to get messages"}, room=sid)


# ==================== TYPING INDICATORS ====================


@sio_server.event
@inject_services(services=["room_service"])
async def typing_start(sid: str, data: dict, room_service: RoomService):
    """Handle typing start indicator"""
    user_info = session_users.get(sid)
    if not user_info:
        return

    user_id = user_info.get("user_id")
    display_name = user_info.get("display_name")
    room_id = data.get("room_id")

    if not room_id:
        return

    try:
        # Verify access to room
        can_access = await room_service.user_can_access_room(UUID(room_id), user_id)
        if not can_access:
            return

        # Broadcast typing indicator to room (excluding sender)
        await sio_server.emit(
            "typing_start",
            {
                "user_id": user_id,
                "display_name": display_name,
                "room_id": room_id,
            },
            room=f"room:{room_id}",
            skip_sid=sid,
        )

    except Exception as e:
        logger.error(f"Error handling typing start for user {user_id}: {e}")


@sio_server.event
@inject_services(services=["room_service"])
async def typing_stop(sid: str, data: dict, room_service: RoomService):
    """Handle typing stop indicator"""
    user_info = session_users.get(sid)
    if not user_info:
        return

    user_id = user_info.get("user_id")
    display_name = user_info.get("display_name")
    room_id = data.get("room_id")

    if not room_id:
        return

    try:
        # Verify access to room
        can_access = await room_service.user_can_access_room(UUID(room_id), user_id)
        if not can_access:
            return

        # Broadcast typing stop to room (excluding sender)
        await sio_server.emit(
            "typing_stop",
            {
                "user_id": user_id,
                "display_name": display_name,
                "room_id": room_id,
            },
            room=f"room:{room_id}",
            skip_sid=sid,
        )

    except Exception as e:
        logger.error(f"Error handling typing stop for user {user_id}: {e}")


# ==================== READ RECEIPTS ====================


@sio_server.event
@inject_services(services=["message_service", "room_service"])
async def mark_messages_read(
    sid: str, data: dict, message_service: MessageService, room_service: RoomService
):
    """Mark messages as read in a room"""
    user_info = session_users.get(sid)
    if not user_info:
        await sio_server.emit("error", {"message": "Not authenticated"}, room=sid)
        return

    user_id = user_info.get("user_id")
    room_id = data.get("room_id")
    message_id = data.get("message_id")

    if not room_id or not message_id:
        await sio_server.emit(
            "error", {"message": "room_id and message_id required"}, room=sid
        )
        return

    try:
        # Verify access to room
        can_access = await room_service.user_can_access_room(UUID(room_id), user_id)
        if not can_access:
            await sio_server.emit(
                "error", {"message": "Access denied to room"}, room=sid
            )
            return

        # Mark messages as read
        success = await message_service.mark_messages_as_read(
            room_id=UUID(room_id), user_id=user_id, message_id=UUID(message_id)
        )

        if success:
            # Notify other room members
            await sio_server.emit(
                "messages_read",
                {
                    "user_id": user_id,
                    "room_id": room_id,
                    "message_id": message_id,
                },
                room=f"room:{room_id}",
                skip_sid=sid,
            )

            await sio_server.emit(
                "messages_marked_read",
                {"room_id": room_id, "message_id": message_id},
                room=sid,
            )

    except Exception as e:
        logger.error(f"Error marking messages read for user {user_id}: {e}")
        await sio_server.emit(
            "error", {"message": "Failed to mark messages as read"}, room=sid
        )


# ==================== UTILITY EVENTS ====================


@sio_server.event
async def ping(sid: str):
    """Handle ping for connection keepalive"""
    await sio_server.emit("pong", {}, room=sid)


@sio_server.event
async def online_users(sid: str):
    """Handle request for online users list"""
    user_info = session_users.get(sid)
    if not user_info:
        return

    online = get_online_users()
    await sio_server.emit("online_users", {"users": online}, room=sid)


@sio_server.event
async def user_status(sid: str, data: dict):
    """Check if specific user is online"""
    user_info = session_users.get(sid)
    if not user_info:
        return

    target_user_id = data.get("user_id")
    is_online = is_user_online(target_user_id)
    await sio_server.emit(
        "user_status", {"user_id": target_user_id, "online": is_online}, room=sid
    )


# ==================== HELPER FUNCTIONS ====================


async def join_user_rooms(
    sid: str, user_id: str, client_id: UUID, room_service: RoomService
):
    """Automatically join user to their rooms when they connect"""
    try:
        rooms = await room_service.get_user_rooms(user_id, client_id)
        for room in rooms:
            room_id = str(room.id)
            await sio_server.enter_room(sid, f"room:{room_id}")
            user_rooms[sid].add(room_id)

        logger.info(f"User {user_id} joined {len(rooms)} rooms")
    except Exception as e:
        logger.error(f"Error joining user {user_id} to rooms: {e}")


def get_user_connection(user_id: str) -> str | None:
    """Get session ID for a connected user"""
    for sid, user_info in session_users.items():
        if user_info and user_info.get("user_id") == user_id:
            return sid
    return None


def is_user_online(user_id: str) -> bool:
    """Check if user is currently online"""
    return get_user_connection(user_id) is not None


def get_online_users() -> list[str]:
    """Get list of online user IDs"""
    online_users = []
    for sid, user_info in session_users.items():  # noqa
        if user_info.get("user_id"):
            online_users.append(user_info["user_id"])
    return online_users


def user_client_info(user_id: str) -> dict | None:
    """Get full connection info for a user"""
    for sid, user_info in session_users.items():
        if user_info.get("user_id") == user_id:
            return {
                "session_id": sid,
                "user_id": user_info.get("user_id"),
                "display_name": user_info.get("display_name"),
                "client_id": user_info.get("client_id"),
                "connection_key": user_info.get("connection_key"),
                "is_scoped": user_info.get("is_scoped", False),
                "rooms": list(user_rooms.get(sid, set())),
            }
    return None


def online_users_by_client(client_id: str) -> list[str]:
    """Get list of online user IDs for a specific client"""
    return [
        user_info["user_id"]
        for user_info in session_users.values()
        if user_info.get("client_id") == client_id and user_info.get("user_id")
    ]


def get_room_members_online(room_id: str) -> list[str]:
    """Get list of online users in a specific room"""
    online_members = []
    for sid, user_info in session_users.items():
        if room_id in user_rooms.get(sid, set()):
            online_members.append(user_info.get("user_id"))
    return online_members


def get_connection_count() -> int:
    """Get total number of active connections"""
    return len(session_users)


def get_user_sessions_info() -> dict:
    """Get detailed info about all active sessions (for debugging)"""
    return {
        "total_connections": len(session_users),
        "active_connections": len(active_connections),
        "sessions": session_users,
        "connection_mappings": active_connections,
        "user_rooms": {sid: list(rooms) for sid, rooms in user_rooms.items()},
    }


async def notify_user_online(user_id: str, client_id: UUID):
    """Notify relevant users that someone came online"""
    await sio_server.emit(
        "user_online",
        {
            "user_id": user_id,
            "client_id": str(client_id),
        },
    )


async def notify_user_offline(user_id: str, client_id: str):
    """Notify relevant users that someone went offline"""
    await sio_server.emit(
        "user_offline",
        {
            "user_id": user_id,
            "client_id": str(client_id),
        },
    )
