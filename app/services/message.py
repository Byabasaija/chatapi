# app/services/message.py
from datetime import datetime

import sqlalchemy
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.messages import Message
from app.schemas.message import MessageCreate, MessageUpdate
from app.services.base import BaseService
from app.sockets.manager import manager


class MessageService(BaseService[Message, MessageCreate, MessageUpdate]):
    def __init__(self, db: AsyncSession):
        super().__init__(model=Message, db=db)

    async def send_message(self, message_data: MessageCreate) -> tuple[Message, bool]:
        """
        Send a message and handle delivery

        Args:
            message_data: Message creation data

        Returns:
            Tuple containing the saved message and delivery status
        """
        # Create and persist message
        message = Message(**message_data.model_dump())
        self.db.add(message)
        await self.db.commit()
        await self.db.refresh(message)

        # Attempt delivery via WebSocket
        delivered = await self._attempt_delivery(message)
        print(
            f"Attempting to deliver message {message.id} to {message.recipient_id}: {delivered}"
        )
        # Update delivery status if successful
        if delivered:
            message.delivered = True
            message.delivered_at = datetime.utcnow()
            await self.db.commit()
            await self.db.refresh(message)

            # Send delivery acknowledgment
            await self._send_delivery_acknowledgment(message)

        return message, delivered

    async def get_chat_history(
        self, sender_id: str, recipient_id: str, limit: int = 100, offset: int = 0
    ) -> list[Message]:
        """
        Get chat history between two users

        Args:
            sender_id: ID of the sender
            recipient_id: ID of the recipient
            limit: Maximum number of messages to return
            offset: Number of messages to skip

        Returns:
            List of messages between the two users
        """
        query = (
            sqlalchemy.select(Message)
            .where(
                sqlalchemy.or_(
                    sqlalchemy.and_(
                        Message.sender_id == sender_id,
                        Message.recipient_id == recipient_id,
                    ),
                    sqlalchemy.and_(
                        Message.sender_id == recipient_id,
                        Message.recipient_id == sender_id,
                    ),
                )
            )
            .order_by(Message.created_at.desc())
            .limit(limit)
            .offset(offset)
        )

        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_user_conversations(self, user_id: str) -> list[dict]:
        """
        Get all conversations for a user with last message info

        Args:
            user_id: ID of the user

        Returns:
            List of conversation summaries with last message details
        """
        # Get all messages where user is sender or recipient
        query = (
            sqlalchemy.select(Message)
            .where(
                sqlalchemy.or_(
                    Message.sender_id == user_id, Message.recipient_id == user_id
                )
            )
            .order_by(Message.created_at.desc())
        )

        result = await self.db.execute(query)
        messages = result.scalars().all()

        # Group by conversation partner
        conversations = {}
        for message in messages:
            partner_id = (
                message.recipient_id
                if message.sender_id == user_id
                else message.sender_id
            )

            if partner_id not in conversations:
                conversations[partner_id] = {
                    "partner_id": partner_id,
                    "last_message": self._message_to_dict(message),
                    "unread_count": 0,
                }

        return list(conversations.values())

    async def mark_messages_as_delivered(self, user_id: str, sender_id: str) -> int:
        """
        Mark messages from a sender to user as delivered

        Args:
            user_id: ID of the recipient
            sender_id: ID of the sender

        Returns:
            Number of messages marked as delivered
        """
        query = (
            sqlalchemy.update(Message)
            .where(
                sqlalchemy.and_(
                    Message.recipient_id == user_id,
                    Message.sender_id == sender_id,
                    Message.delivered is False,
                )
            )
            .values(delivered=True, delivered_at=datetime.utcnow())
        )

        result = await self.db.execute(query)
        await self.db.commit()
        return result.rowcount

    def _message_to_dict(self, message: Message) -> dict:
        """Serialize a Message SQLAlchemy object to a dictionary."""
        return {
            "id": str(message.id),
            "sender_id": message.sender_id,
            "recipient_id": message.recipient_id,
            "group_id": message.group_id,
            "encrypted_payload": message.encrypted_payload,
            "content": message.content,
            "content_type": message.content_type,
            "custom_metadata": message.custom_metadata,
            "created_at": message.created_at.isoformat()
            if message.created_at
            else None,
            "delivered": message.delivered,
            "delivered_at": message.delivered_at.isoformat()
            if message.delivered_at
            else None,
        }

    async def _attempt_delivery(self, message: Message) -> bool:
        """Attempt to deliver message via WebSocket"""
        message_dict = self._message_to_dict(message)
        return await manager.send_message(message_data=message_dict)

    async def _send_delivery_acknowledgment(self, message: Message) -> None:
        """Send delivery acknowledgment to sender"""
        try:
            ack_data = {
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
                data=ack_data, sender_id=message.sender_id
            )
        except Exception:
            # Log error in production
            pass


def get_message_service(db: AsyncSession) -> MessageService:
    """Factory function for dependency injection"""
    return MessageService(db)
