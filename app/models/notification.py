from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING
from uuid import uuid4

from sqlalchemy import (
    JSON,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.base_class import Base

if TYPE_CHECKING:
    from app.models.client import Client


class NotificationType(str, Enum):
    """Types of notifications supported by the system."""

    EMAIL = "email"
    WEBSOCKET = "websocket"
    # SMS = "sms"  # Future extension


class NotificationStatus(str, Enum):
    """Status of notification processing."""

    PENDING = "pending"
    PROCESSING = "processing"
    SENT = "sent"
    FAILED = "failed"
    RETRYING = "retrying"
    CANCELLED = "cancelled"


class NotificationPriority(str, Enum):
    """Priority levels for notification processing."""

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class Notification(Base):
    """
    Main notification record that tracks all notifications sent through the system.
    Acts as the central record for notification lifecycle management.
    """

    __tablename__ = "notifications"

    id: Mapped[str] = mapped_column(
        PGUUID,
        primary_key=True,
        default=uuid4,
        server_default=text("gen_random_uuid()"),
    )

    # Client association
    client_id: Mapped[str] = mapped_column(
        PGUUID, ForeignKey("clients.id"), nullable=False
    )
    client: Mapped["Client"] = relationship("Client", back_populates="notifications")

    # Notification configuration
    type: Mapped[NotificationType] = mapped_column(String(20), nullable=False)
    priority: Mapped[NotificationPriority] = mapped_column(
        String(10), default=NotificationPriority.NORMAL, nullable=False
    )

    # Content
    subject: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    meta: Mapped[dict | None] = mapped_column(JSON)

    # Email-specific fields
    to_email: Mapped[str | None] = mapped_column(String(255))
    from_email: Mapped[str | None] = mapped_column(String(255))
    reply_to: Mapped[str | None] = mapped_column(String(255))
    cc: Mapped[list | None] = mapped_column(JSON)
    bcc: Mapped[list | None] = mapped_column(JSON)

    # WebSocket-specific fields
    room_id: Mapped[str | None] = mapped_column(PGUUID)

    # Email fallback for WebSocket notifications
    email_fallback: Mapped[dict | None] = mapped_column(JSON)

    # Delivery configuration
    max_retry_attempts: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    retry_attempt: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Status tracking
    status: Mapped[NotificationStatus] = mapped_column(
        String(20), default=NotificationStatus.PENDING, nullable=False
    )

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
    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Error tracking
    error_message: Mapped[str | None] = mapped_column(Text)

    # Relationships
    delivery_attempts: Mapped[list["NotificationDeliveryAttempt"]] = relationship(
        "NotificationDeliveryAttempt",
        back_populates="notification",
        cascade="all, delete-orphan",
    )

    # Indexes for performance
    __table_args__ = (
        Index("ix_notifications_client_id", "client_id"),
        Index("ix_notifications_status", "status"),
        Index("ix_notifications_type", "notification_type"),
        Index("ix_notifications_created_at", "created_at"),
        Index("ix_notifications_scheduled_at", "scheduled_at"),
        Index("ix_notifications_priority", "priority"),
    )


class NotificationDeliveryAttempt(Base):
    """
    Records each delivery attempt for a notification.
    Provides detailed tracking of delivery success/failure.
    """

    __tablename__ = "notification_delivery_attempts"

    id: Mapped[str] = mapped_column(
        PGUUID,
        primary_key=True,
        default=uuid4,
        server_default=text("gen_random_uuid()"),
    )

    # Parent notification
    notification_id: Mapped[str] = mapped_column(
        PGUUID, ForeignKey("notifications.id"), nullable=False
    )
    notification: Mapped["Notification"] = relationship(
        "Notification", back_populates="delivery_attempts"
    )

    # Attempt details
    attempt_number: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # success, failed, timeout

    # Provider-specific information
    provider_name: Mapped[str | None] = mapped_column(String(50))
    provider_response: Mapped[dict | None] = mapped_column(JSON)
    provider_message_id: Mapped[str | None] = mapped_column(String(255))

    # Timing
    attempted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    response_time_ms: Mapped[int | None] = mapped_column(Integer)

    # Error details
    error_code: Mapped[str | None] = mapped_column(String(50))
    error_message: Mapped[str | None] = mapped_column(Text)

    # Indexes
    __table_args__ = (
        Index("ix_delivery_attempts_notification_id", "notification_id"),
        Index("ix_delivery_attempts_status", "status"),
        Index("ix_delivery_attempts_attempted_at", "attempted_at"),
    )
