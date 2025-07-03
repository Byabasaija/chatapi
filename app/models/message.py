from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Optional
from uuid import uuid4

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates
from sqlalchemy.sql import func

from app.db.base_class import Base

if TYPE_CHECKING:
    from app.models.room import Room


class ContentType(str, Enum):
    text = "text"
    image = "image"
    file = "file"
    video = "video"
    audio = "audio"
    document = "document"


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[str] = mapped_column(
        PGUUID,
        primary_key=True,
        default=uuid4,
        server_default=text("gen_random_uuid()"),
    )
    room_id: Mapped[str] = mapped_column(
        PGUUID, ForeignKey("rooms.id", ondelete="CASCADE"), nullable=False
    )
    # Note: sender info comes from scoped key authentication context
    content: Mapped[str | None] = mapped_column(Text)
    content_type: Mapped[str] = mapped_column(
        String(20), default=ContentType.text.value, nullable=False
    )

    # File/Media metadata
    file_url: Mapped[str | None] = mapped_column(String(500))
    file_name: Mapped[str | None] = mapped_column(String(255))
    file_size: Mapped[int | None] = mapped_column(Integer)
    file_mime_type: Mapped[str | None] = mapped_column(String(100))

    # Message metadata
    reply_to_id: Mapped[str | None] = mapped_column(
        PGUUID, ForeignKey("messages.id", ondelete="SET NULL"), nullable=True
    )
    is_edited: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Metadata stored at message creation time (from auth context)
    sender_user_id: Mapped[str] = mapped_column(String(255), nullable=False)
    sender_display_name: Mapped[str] = mapped_column(String(100), nullable=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    edited_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Relationships
    room: Mapped["Room"] = relationship("Room", back_populates="messages")
    reply_to: Mapped[Optional["Message"]] = relationship(
        "Message", remote_side=[id], back_populates="replies"
    )
    replies: Mapped[list["Message"]] = relationship(
        "Message", back_populates="reply_to"
    )

    @validates("content_type")
    def validate_content_type(self, key, value):
        if isinstance(value, str) and value not in [e.value for e in ContentType]:
            raise ValueError(f"Invalid content type: {value}")
        return value

    def mark_as_edited(self):
        """Mark message as edited"""
        self.is_edited = True
        self.edited_at = func.now()
        self.updated_at = func.now()

    def soft_delete(self):
        """Soft delete the message"""
        self.is_deleted = True
        self.content = None  # Clear content for privacy
        self.updated_at = func.now()

    __table_args__ = (
        Index("idx_messages_room_id", "room_id"),
        Index("idx_messages_sender_user_id", "sender_user_id"),
        Index("idx_messages_created_at", "created_at"),
        Index("idx_messages_content_type", "content_type"),
        Index("idx_messages_is_deleted", "is_deleted"),
        Index("idx_messages_reply_to_id", "reply_to_id"),
        # Composite index for room message pagination
        Index("idx_messages_room_created", "room_id", "created_at"),
        # Index for unread message queries
        Index("idx_messages_room_active", "room_id", "is_deleted", "created_at"),
    )
