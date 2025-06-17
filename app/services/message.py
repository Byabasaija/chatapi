# app/services/message.py
from datetime import datetime

import sqlalchemy
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.messages import Message
from app.schemas.message import MessageCreate, MessageUpdate
from app.services.base import BaseService


class MessageService(BaseService[Message, MessageCreate, MessageUpdate]):
    def __init__(self, db: AsyncSession):
        super().__init__(model=Message, db=db)

    async def save_message(self, message_data: MessageCreate) -> Message:
        """
        Save a message to the database

        Args:
            message_data: Message creation data

        Returns:
            The saved message object
        """
        message = Message(**message_data.model_dump())
        self.db.add(message)
        await self.db.commit()
        await self.db.refresh(message)
        return message

    async def mark_message_delivered(self, message_id: str) -> bool:
        """
        Mark a message as delivered

        Args:
            message_id: ID of the message to mark as delivered

        Returns:
            True if message was updated, False otherwise
        """
        try:
            query = (
                sqlalchemy.update(Message)
                .where(Message.id == message_id)
                .values(
                    delivered=True,
                    delivered_at=datetime.utcnow(),
                )
            )

            result = await self.db.execute(query)
            await self.db.commit()
            return result.rowcount > 0

        except Exception as e:
            await self.db.rollback()
            raise e

    async def get_undelivered_messages(self, user_id: str) -> list[dict]:
        """
        Get undelivered messages for a user

        Args:
            user_id: ID of the user

        Returns:
            List of undelivered messages
        """
        query = (
            sqlalchemy.select(Message)
            .where(
                sqlalchemy.and_(
                    Message.recipient_id == user_id, Message.delivered is False
                )
            )
            .order_by(Message.created_at.asc())
        )

        result = await self.db.execute(query)
        messages = result.scalars().all()
        return [self._message_to_dict(msg) for msg in messages]

    async def get_chat_history(
        self, sender_id: str, recipient_id: str, limit: int = 100, offset: int = 0
    ) -> list[dict]:
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
        messages = result.scalars().all()
        return [self._message_to_dict(msg) for msg in messages]

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
                    "partner_name": (
                        message.recipient_name
                        if message.sender_id == user_id
                        else message.sender_name
                    ),
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
            "sender_name": message.sender_name,
            "recipient_name": message.recipient_name,
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


def get_message_service(db: AsyncSession) -> MessageService:
    """Factory function for dependency injection"""
    return MessageService(db)
