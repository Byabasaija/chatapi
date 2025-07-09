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
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates
from sqlalchemy.sql import func

from app.db.base_class import Base

if TYPE_CHECKING:
    from app.models.client import Client
    from app.models.message import Message


# Room inactivity settings by room type (in days)
ROOM_INACTIVITY_SETTINGS = {
    "direct": 90,  # 3 months for direct messages
    "group": 30,  # 1 month for group chats
    "channel": 180,  # 6 months for channels
    "support": 7,  # 1 week for support rooms
}


class RoomType(str, Enum):
    direct = "direct"  # 1-on-1 conversation
    group = "group"  # Group chat
    channel = "channel"  # Broadcast channel
    support = "support"  # Support/helpdesk rooms


class MemberRole(str, Enum):
    owner = "owner"
    admin = "admin"
    member = "member"


class Room(Base):
    __tablename__ = "rooms"

    id: Mapped[str] = mapped_column(
        PGUUID,
        primary_key=True,
        default=uuid4,
        server_default=text("gen_random_uuid()"),
    )
    client_id: Mapped[str] = mapped_column(
        PGUUID, ForeignKey("clients.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str | None] = mapped_column(String(100))
    description: Mapped[str | None] = mapped_column(Text)
    room_type: Mapped[str] = mapped_column(
        String(20), default=RoomType.group.value, nullable=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    max_members: Mapped[int | None] = mapped_column(Integer, default=100)
    created_by_user_id: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    last_message_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Auto-deactivation fields
    deactivated_reason: Mapped[str | None] = mapped_column(
        String(50)
    )  # "manual", "auto_inactive", "expired"
    deactivated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Relationships - use string references to avoid circular imports
    client: Mapped["Client"] = relationship("Client", back_populates="rooms")
    memberships: Mapped[list["RoomMembership"]] = relationship(
        "RoomMembership", back_populates="room", cascade="all, delete-orphan"
    )
    messages: Mapped[list["Message"]] = relationship(
        "Message", back_populates="room", cascade="all, delete-orphan"
    )

    @validates("room_type")
    def validate_room_type(self, key, value):
        if isinstance(value, str) and value not in [e.value for e in RoomType]:
            raise ValueError(f"Invalid room type: {value}")
        return value

    __table_args__ = (
        Index("idx_rooms_client_id", "client_id"),
        Index("idx_rooms_room_type", "room_type"),
        Index("idx_rooms_is_active", "is_active"),
        Index("idx_rooms_last_message_at", "last_message_at"),
        Index("idx_rooms_created_by_user_id", "created_by_user_id"),
    )


class RoomMembership(Base):
    __tablename__ = "room_memberships"

    id: Mapped[str] = mapped_column(
        PGUUID,
        primary_key=True,
        default=uuid4,
        server_default=text("gen_random_uuid()"),
    )
    room_id: Mapped[str] = mapped_column(
        PGUUID, ForeignKey("rooms.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[str] = mapped_column(
        String(255), nullable=False
    )  # From integrating client
    display_name: Mapped[str] = mapped_column(String(100), nullable=False)
    role: Mapped[str] = mapped_column(
        String(20), default=MemberRole.member.value, nullable=False
    )
    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    left_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_read_message_id: Mapped[str | None] = mapped_column(
        PGUUID, ForeignKey("messages.id", ondelete="SET NULL"), nullable=True
    )
    last_read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Relationships - use string references
    room: Mapped["Room"] = relationship("Room", back_populates="memberships")
    last_read_message: Mapped[Optional["Message"]] = relationship(
        "Message", foreign_keys=[last_read_message_id]
    )

    @validates("role")
    def validate_role(self, key, value):
        if isinstance(value, str) and value not in [e.value for e in MemberRole]:
            raise ValueError(f"Invalid member role: {value}")
        return value

    def update_display_name(self, new_display_name: str):
        """Update display name for this room membership"""
        self.display_name = new_display_name
        self.updated_at = func.now()

    def mark_as_read(self, message_id: str):
        """Mark messages as read up to the specified message"""
        self.last_read_message_id = message_id
        self.last_read_at = func.now()

    __table_args__ = (
        UniqueConstraint("room_id", "user_id", name="uq_room_user_membership"),
        Index("idx_room_memberships_room_id", "room_id"),
        Index("idx_room_memberships_user_id", "user_id"),
        Index("idx_room_memberships_is_active", "is_active"),
        Index("idx_room_memberships_role", "role"),
        Index("idx_room_memberships_last_read_message_id", "last_read_message_id"),
    )
