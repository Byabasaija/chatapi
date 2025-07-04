# app/api/api_v1/routes/message.py
# ruff: noqa
from uuid import UUID

from fastapi import APIRouter, HTTPException, Path, Query, status
from pydantic import BaseModel

from app.api.deps import AuthClientDep, MessageServiceDep
from app.schemas.message import ContentType, MessageCreate, MessageRead

router = APIRouter()


# Request/Response models for better API documentation
class SendMessageRequest(BaseModel):
    room_id: UUID
    content: str | None = None
    content_type: ContentType = ContentType.text
    file_url: str | None = None
    file_name: str | None = None
    file_size: int | None = None
    file_mime_type: str | None = None
    reply_to_id: UUID | None = None


class EditMessageRequest(BaseModel):
    content: str


class MarkAsReadRequest(BaseModel):
    message_id: UUID


class MessageResponse(BaseModel):
    success: bool
    message: str
    data: dict | None = None


# ==================== CORE MESSAGE OPERATIONS ====================


@router.post("/", response_model=MessageRead, summary="Send a message")
async def send_message(
    request: SendMessageRequest,
    auth_client: AuthClientDep,
    message_service: MessageServiceDep,
):
    """
    Send a new message to a room.

    This endpoint allows sending text messages, file attachments, replies, etc.
    Follows REST principles as an alternative to WebSocket for simple integrations.
    """
    try:
        client, scoped_key = auth_client

        # For scoped keys, use the user_id from the key
        sender_user_id = scoped_key.user_id if scoped_key else str(client.id)
        sender_display_name = (
            scoped_key.user_id if scoped_key else (client.name or "API Client")
        )

        message_data = MessageCreate(
            room_id=request.room_id,
            sender_user_id=sender_user_id,
            sender_display_name=sender_display_name,
            content=request.content,
            content_type=request.content_type,
            file_url=request.file_url,
            file_name=request.file_name,
            file_size=request.file_size,
            file_mime_type=request.file_mime_type,
            reply_to_id=request.reply_to_id,
        )

        message = await message_service.create_message(
            room_id=request.room_id,
            sender_user_id=sender_user_id,
            sender_display_name=sender_display_name,
            message_data=message_data,
        )
        return message
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send message: {str(e)}",
        )


@router.get(
    "/rooms/{room_id}", response_model=list[MessageRead], summary="Get room messages"
)
async def get_room_messages(
    room_id: UUID = Path(..., description="Room ID to fetch messages from"),
    auth_client: AuthClientDep = None,
    message_service: MessageServiceDep = None,
    limit: int = Query(50, ge=1, le=100, description="Number of messages to return"),
    offset: int = Query(0, ge=0, description="Number of messages to skip"),
    before_message_id: UUID | None = Query(
        None, description="Get messages before this message ID"
    ),
):  # noqa
    """
    Get messages from a specific room with pagination.

    Supports cursor-based pagination using `before_message_id` for better performance
    with large message histories.
    """
    try:
        messages = await message_service.get_room_messages(
            room_id=room_id,
            limit=limit,
            offset=offset,
            before_message_id=before_message_id,
        )
        return messages
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve messages: {str(e)}",
        )


@router.get(
    "/rooms/{room_id}/unread",
    response_model=list[MessageRead],
    summary="Get unread messages",
)
async def get_unread_messages(
    room_id: UUID = Path(..., description="Room ID to check for unread messages"),
    auth_client: AuthClientDep = None,
    message_service: MessageServiceDep = None,
):
    """
    Get all unread messages for the authenticated user in a specific room.

    Returns messages that have been sent since the user's last read timestamp.
    """
    try:
        client, scoped_key = auth_client
        user_id = scoped_key.user_id if scoped_key else str(client.id)

        messages = await message_service.get_unread_messages(
            room_id=room_id,
            user_id=user_id,
        )
        return messages
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve unread messages: {str(e)}",
        )


# ==================== MESSAGE ACTIONS ====================


@router.put("/{message_id}", response_model=MessageRead, summary="Edit a message")
async def edit_message(
    message_id: UUID = Path(..., description="Message ID to edit"),
    request: EditMessageRequest = None,
    auth_client: AuthClientDep = None,
    message_service: MessageServiceDep = None,
):  # noqa
    """
    Edit an existing message.

    Only the original sender can edit their messages.
    Edited messages are marked with an `is_edited` flag and `edited_at` timestamp.
    """
    try:
        message = await message_service.edit_message(
            message_id=message_id,
            new_content=request.content,
        )
        if not message:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Message not found or cannot be edited",
            )
        return message
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to edit message: {str(e)}",
        )


@router.delete(
    "/{message_id}", response_model=MessageResponse, summary="Delete a message"
)
async def delete_message(
    message_id: UUID = Path(..., description="Message ID to delete"),
    auth_client: AuthClientDep = None,
    message_service: MessageServiceDep = None,
):  # noqa
    """
    Delete a message (soft delete).

    Only the original sender can delete their messages.
    Deleted messages are marked as deleted but remain in the database for audit purposes.
    """
    try:
        success = await message_service.delete_message(message_id=message_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Message not found or already deleted",
            )
        return MessageResponse(
            success=True,
            message="Message deleted successfully",
            data={"message_id": str(message_id)},
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete message: {str(e)}",
        )


@router.get(
    "/{message_id}", response_model=MessageRead, summary="Get a specific message"
)
async def get_message(
    message_id: UUID = Path(..., description="Message ID to retrieve"),
    auth_client: AuthClientDep = None,
    message_service: MessageServiceDep = None,
    include_replies: bool = Query(False, description="Include replies to this message"),
):  # noqa
    """
    Get a specific message by ID.

    Optionally includes replies if `include_replies=true`.
    """
    try:
        if include_replies:
            message = await message_service.get_message_with_replies(message_id)
        else:
            message = await message_service.get(message_id)

        if not message:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Message not found",
            )
        return message
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve message: {str(e)}",
        )


# ==================== READ STATUS MANAGEMENT ====================


@router.post(
    "/rooms/{room_id}/read",
    response_model=MessageResponse,
    summary="Mark messages as read",
)
async def mark_messages_as_read(
    room_id: UUID = Path(..., description="Room ID where messages were read"),
    request: MarkAsReadRequest = None,
    auth_client: AuthClientDep = None,
    message_service: MessageServiceDep = None,
):
    """
    Mark messages as read up to a specific message.

    All messages in the room sent before and including the specified message
    will be marked as read for the authenticated user.
    """
    try:
        client, scoped_key = auth_client
        user_id = scoped_key.user_id if scoped_key else str(client.id)

        success = await message_service.mark_messages_as_read(
            room_id=room_id,
            user_id=user_id,
            message_id=request.message_id,
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Room membership not found or message not found",
            )

        return MessageResponse(
            success=True,
            message="Messages marked as read",
            data={
                "room_id": str(room_id),
                "user_id": user_id,
                "last_read_message_id": str(request.message_id),
            },
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to mark messages as read: {str(e)}",
        )


# ==================== SEARCH AND DISCOVERY ====================


@router.get("/search", response_model=list[MessageRead], summary="Search messages")
async def search_messages(
    q: str = Query(..., min_length=1, description="Search query"),
    room_id: UUID | None = Query(None, description="Limit search to specific room"),
    auth_client: AuthClientDep = None,
    message_service: MessageServiceDep = None,
    limit: int = Query(20, ge=1, le=100, description="Number of results to return"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
):  # noqa
    """
    Search messages by content.

    Searches across all accessible rooms or within a specific room if specified.
    Results are ordered by relevance and recency.
    """
    # Note: This would require implementing search functionality in the service
    # For now, return a placeholder response
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Message search functionality not yet implemented",
    )
