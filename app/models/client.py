from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING
from uuid import uuid4

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSON
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates
from sqlalchemy.sql import func

from app.db.base_class import Base

if TYPE_CHECKING:
    from app.models.notification import Notification
    from app.models.room import Room


class ScopedKeyPermission(str, Enum):
    READ_MESSAGES = "read_messages"
    SEND_MESSAGES = "send_messages"
    MANAGE_ROOMS = "manage_rooms"
    INVITE_USERS = "invite_users"


class Client(Base):
    __tablename__ = "clients"

    id: Mapped[str] = mapped_column(
        PGUUID,
        primary_key=True,
        default=uuid4,
    )
    name: Mapped[str | None] = mapped_column(String(255))
    master_api_key: Mapped[str] = mapped_column(
        String(255), nullable=False, unique=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Email provider configurations (client-specific)
    email_provider_configs: Mapped[list[dict] | None] = mapped_column(
        JSON, nullable=True, default=list
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    scoped_keys: Mapped[list["ScopedKey"]] = relationship(
        "ScopedKey", back_populates="client", cascade="all, delete-orphan"
    )
    rooms: Mapped[list["Room"]] = relationship(
        "Room", back_populates="client", cascade="all, delete-orphan"
    )
    notifications: Mapped[list["Notification"]] = relationship(
        "Notification", back_populates="client", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_clients_master_api_key", "master_api_key"),
        Index("idx_clients_is_active", "is_active"),
    )


class ScopedKey(Base):
    __tablename__ = "scoped_keys"

    id: Mapped[str] = mapped_column(
        PGUUID,
        primary_key=True,
        default=uuid4,
    )
    client_id: Mapped[str] = mapped_column(
        PGUUID, ForeignKey("clients.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[str] = mapped_column(
        String(255), nullable=False
    )  # From integrating client
    scoped_api_key: Mapped[str] = mapped_column(
        String(255), nullable=False, unique=True
    )
    permissions: Mapped[list[str]] = mapped_column(
        ARRAY(String), nullable=False, default=list
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    client: Mapped["Client"] = relationship("Client", back_populates="scoped_keys")

    @validates("permissions")
    def validate_permissions(self, key, value):
        valid_permissions = [e.value for e in ScopedKeyPermission]
        if isinstance(value, list):
            for perm in value:
                if perm not in valid_permissions:
                    raise ValueError(f"Invalid permission: {perm}")
        return value

    __table_args__ = (
        UniqueConstraint("client_id", "user_id", name="uq_client_user_scoped_key"),
        Index("idx_scoped_keys_client_id", "client_id"),
        Index("idx_scoped_keys_user_id", "user_id"),
        Index("idx_scoped_keys_api_key", "scoped_api_key"),
        Index("idx_scoped_keys_is_active", "is_active"),
    )
