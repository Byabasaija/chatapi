from sqlmodel import Session, select

from app.models.messages import Message
from app.sockets.manager import manager


async def handle_incoming_message(session: Session, message_data: dict):
    # 1. Persist message
    message = Message(**message_data)
    print(f"Persisting message: {message}")
    with session:
        session.add(message)
        session.commit()
        session.refresh(message)

    # 2. Forward if recipient is connected
    send = await manager.send_message(message.model_dump(mode="json"))
    # update delivered status to true
    if send:
        message.delivered = True
        message.delivered_at = message.created_at
        with session:
            session.add(message)
            session.commit()
            session.refresh(message)
        # send delivery receipt
        data = {
            "content": message.content,
            "encrypted_payload": message.encrypted_payload,
            "content_type": message.content_type,
            "sender_id": message.sender_id,
            "recipient_id": message.recipient_id,
            "delivered": message.delivered,
            "delivered_at": message.delivered_at.isoformat()
            if message.delivered_at
            else None,
            "created_at": message.created_at.isoformat()
            if message.created_at
            else None,
        }
        await manager.send_acknowledgment(
            data=data,
            sender_id=message.sender_id,
        )


# create a function to get a session based on messages. eg a session with a specific user. When i say session i mean a conversation session. something that is like a chat history.
# this function should return a list of messages between the two users. it should take in two user ids and return a list of messages between them.
def get_chat_history(session: Session, sender_id: str, recipient_id: str):
    with session:
        messages = (
            session.exec(Message)
            .filter(
                (Message.sender_id == sender_id)
                & (Message.recipient_id == recipient_id)
            )
            .all()
        )
    return messages


# create a function that will a users conversations. Somthing like a users rooms?
def get_user_conversations(session: Session, user_id: str):
    statement = select(Message).where(
        (Message.sender_id == user_id) | (Message.recipient_id == user_id)
    )
    results = session.exec(statement)
    messages = results.all()
    return messages
