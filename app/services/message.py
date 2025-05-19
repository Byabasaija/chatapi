from sqlmodel import Session

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
    send = await manager.send_message(message.model_dump())
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
            "delivered_at": message.delivered_at,
            "created_at": message.created_at,
        }
        await manager.send_acknowledgment(
            data=data,
            sender_id=message.sender_id,
        )
