from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.api.deps import get_db
from app.models.api_client import APIClientCreate, APIClientReadWithKey
from app.services.client import register_new_client
from app.services.message import get_chat_history, get_user_conversations

router = APIRouter()


@router.post("/register", response_model=APIClientReadWithKey)
def register_client(payload: APIClientCreate, session: Session = Depends(get_db)):
    client, raw_key = register_new_client(payload, session)
    return {
        "id": client.id,
        "created_at": client.created_at,
        "name": client.name,
        "api_key": raw_key,
    }


# create a route to get the get_user_conversations
@router.get("/conversations")
async def user_conversations(
    user_id: str,
    session: Session = Depends(get_db),
):
    messages = await get_user_conversations(session, user_id)
    return messages


# create a route to get the get_chat_history
@router.get("/history")
async def chat_history(
    sender_id: str,
    recipient_id: str,
    session: Session = Depends(get_db),
):
    messages = await get_chat_history(session, sender_id, recipient_id)
    return messages
