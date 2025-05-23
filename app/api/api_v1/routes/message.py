from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.api.deps import get_async_db
from app.services.message import get_chat_history, get_user_conversations

router = APIRouter()


# create a route to get the get_user_conversations
@router.get("/conversations")
async def user_conversations(
    user_id: str,
    session: Session = Depends(get_async_db),
):
    messages = await get_user_conversations(session, user_id)
    return messages


# create a route to get the get_chat_history
@router.get("/history")
async def chat_history(
    sender_id: str,
    recipient_id: str,
    session: Session = Depends(get_async_db),
):
    messages = await get_chat_history(session, sender_id, recipient_id)
    return messages
