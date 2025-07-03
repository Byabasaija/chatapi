# app/services/message.py
from uuid import UUID

import sqlalchemy
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.message import Message
from app.models.room import Room, RoomMembership
from app.schemas.message import MessageCreate, MessageUpdate
from app.services.base import BaseService


class MessageService(BaseService[Message, MessageCreate, MessageUpdate]):
    def __init__(self, db: AsyncSession):
        super().__init__(model=Message, db=db)

    async def create_message(
        self,
        room_id: UUID,
        sender_user_id: str,
        sender_display_name: str,
        message_data: MessageCreate,
    ) -> Message:
        """
        Create a new message in a room

        Args:
            room_id: The room ID
            sender_user_id: User ID of the sender
            sender_display_name: Display name of the sender
            message_data: Message creation data

        Returns:
            Created message object
        """
        # Create message
        message = Message(
            room_id=room_id,
            sender_user_id=sender_user_id,
            sender_display_name=sender_display_name,
            content=message_data.content,
            content_type=message_data.content_type.value,
            file_url=message_data.file_url,
            file_name=message_data.file_name,
            file_size=message_data.file_size,
            file_mime_type=message_data.file_mime_type,
            reply_to_id=message_data.reply_to_id,
        )

        self.db.add(message)
        await self.db.commit()
        await self.db.refresh(message)

        # Update room's last message timestamp
        await self.db.execute(
            sqlalchemy.update(Room)
            .where(Room.id == room_id)
            .values(last_message_at=sqlalchemy.func.now())
        )
        await self.db.commit()

        return message

    async def get_room_messages(
        self,
        room_id: UUID,
        limit: int = 50,
        offset: int = 0,
        before_message_id: UUID | None = None,
    ) -> list[Message]:
        """Get messages from a room with pagination"""
        query = (
            sqlalchemy.select(Message)
            .where(Message.room_id == room_id)
            .where(Message.is_deleted is False)
            .order_by(Message.created_at.desc())
        )

        if before_message_id:
            # Get messages before a specific message (for pagination)
            before_message = await self.get(id=before_message_id)
            if before_message:
                query = query.where(Message.created_at < before_message.created_at)

        query = query.limit(limit).offset(offset)

        result = await self.db.execute(query)
        messages = result.scalars().all()

        # Return in chronological order
        return list(reversed(messages))

    async def get_unread_messages(self, room_id: UUID, user_id: str) -> list[Message]:
        """Get unread messages for a user in a room"""
        # Get user's last read message
        membership_result = await self.db.execute(
            sqlalchemy.select(RoomMembership)
            .where(RoomMembership.room_id == room_id)
            .where(RoomMembership.user_id == user_id)
            .where(RoomMembership.is_active is True)
        )
        membership = membership_result.scalar_one_or_none()

        if not membership:
            return []

        query = (
            sqlalchemy.select(Message)
            .where(Message.room_id == room_id)
            .where(Message.is_deleted is False)
            .where(Message.sender_user_id != user_id)  # Don't include own messages
            .order_by(Message.created_at.asc())
        )

        if membership.last_read_message_id:
            # Get messages after last read message
            last_read_result = await self.db.execute(
                sqlalchemy.select(Message.created_at).where(
                    Message.id == membership.last_read_message_id
                )
            )
            last_read_time = last_read_result.scalar_one_or_none()
            if last_read_time:
                query = query.where(Message.created_at > last_read_time)

        result = await self.db.execute(query)
        return result.scalars().all()

    async def mark_messages_as_read(
        self, room_id: UUID, user_id: str, message_id: UUID
    ) -> bool:
        """Mark messages as read up to a specific message"""
        # Update room membership
        result = await self.db.execute(
            sqlalchemy.update(RoomMembership)
            .where(RoomMembership.room_id == room_id)
            .where(RoomMembership.user_id == user_id)
            .where(RoomMembership.is_active is True)
            .values(last_read_message_id=message_id, last_read_at=sqlalchemy.func.now())
        )
        await self.db.commit()

        return result.rowcount > 0

    async def edit_message(self, message_id: UUID, new_content: str) -> Message | None:
        """Edit a message"""
        message = await self.get(id=message_id)
        if message and not message.is_deleted:
            message.content = new_content
            message.mark_as_edited()
            await self.db.commit()
            await self.db.refresh(message)
            return message
        return None

    async def delete_message(self, message_id: UUID) -> bool:
        """Soft delete a message"""
        message = await self.get(id=message_id)
        if message and not message.is_deleted:
            message.soft_delete()
            await self.db.commit()
            return True
        return False

    async def get_message_with_replies(self, message_id: UUID) -> Message | None:
        """Get a message with its replies"""
        result = await self.db.execute(
            sqlalchemy.select(Message)
            .where(Message.id == message_id)
            .options(selectinload(Message.replies))
        )
        return result.scalar_one_or_none()


def get_message_service(db: AsyncSession) -> MessageService:
    return MessageService(db)
