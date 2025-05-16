from sqlmodel import Session

from app.models.messages import Message
from app.sockets.manager import manager


async def handle_incoming_message(session: Session, message_data: dict):
    # 1. Persist message
    message = Message(**message_data)
    with session:
        session.add(message)
        session.commit()
        session.refresh(message)

    # 2. Forward if recipient is connected
    await manager.send_message({"msg": "message", "data": message.model_dump()})
