# app/api/api_v1/routes/message.py

from fastapi import APIRouter, HTTPException, Query, status

from app.api.deps import MessageServiceDep
from app.schemas.message import ConversationSummary, MessageCreate, MessageRead

router = APIRouter()


@router.get("/conversations", response_model=list[ConversationSummary])
async def get_user_conversations(
    user_id: str,
    message_service: MessageServiceDep,
):
    """
    Get all conversations for a user with last message and unread count
    """
    try:
        conversations = await message_service.get_user_conversations(user_id)
        return conversations
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve conversations",
        )


@router.get("/history", response_model=list[MessageRead])
async def get_chat_history(
    sender_id: str,
    recipient_id: str,
    message_service: MessageServiceDep,
    limit: int = Query(
        default=100, ge=1, le=500, description="Number of messages to return"
    ),
    offset: int = Query(default=0, ge=0, description="Number of messages to skip"),
):
    """
    Get chat history between two users with pagination
    """
    try:
        messages = await message_service.get_chat_history(
            sender_id=sender_id, recipient_id=recipient_id, limit=limit, offset=offset
        )
        return messages
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve chat history",
        )


@router.post("/send", response_model=MessageRead)
async def send_message(
    message_data: MessageCreate,
    message_service: MessageServiceDep,
):
    """
    Send a message (alternative to WebSocket for REST clients)
    """
    # try:
    message, delivered = await message_service.send_message(message_data)
    return message
    # except Exception:
    #     raise HTTPException(
    #         status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    #         detail="Failed to send message",
    #     )


@router.put("/mark-delivered")
async def mark_messages_as_delivered(
    user_id: str,
    sender_id: str,
    message_service: MessageServiceDep,
):
    """
    Mark all messages from a sender as delivered
    """
    try:
        count = await message_service.mark_messages_as_delivered(
            user_id=user_id, sender_id=sender_id
        )
        return {"marked_as_delivered": count}
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to mark messages as delivered",
        )
