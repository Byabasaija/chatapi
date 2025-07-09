from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING
from uuid import uuid4

from sqlalchemy import (
    JSON,
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
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.base_class import Base

if TYPE_CHECKING:
    from app.models.client import Client


class WebhookEventType(str, Enum):
    """Types of webhook events supported by the system."""

    MESSAGE_CREATED = "message.created"
    MESSAGE_UPDATED = "message.updated"
    MESSAGE_DELETED = "message.deleted"
    ROOM_CREATED = "room.created"
    ROOM_UPDATED = "room.updated"
    ROOM_DELETED = "room.deleted"
    USER_JOINED = "user.joined"
    USER_LEFT = "user.left"
    NOTIFICATION_SENT = "notification.sent"
    NOTIFICATION_FAILED = "notification.failed"
    CUSTOM = "custom"  # For client-defined events


class WebhookStatus(str, Enum):
    """Status of webhook endpoints."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"  # Temporarily disabled due to failures
    PENDING_VERIFICATION = "pending_verification"


class WebhookDeliveryStatus(str, Enum):
    """Status of webhook delivery attempts."""

    PENDING = "pending"
    DELIVERING = "delivering"
    SUCCESS = "success"
    FAILED = "failed"
    RETRYING = "retrying"
    ABANDONED = "abandoned"  # Max retries exceeded


class WebhookEndpoint(Base):
    """
    Webhook endpoints registered by clients to receive event notifications.
    """

    __tablename__ = "webhook_endpoints"

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
    client: Mapped["Client"] = relationship(
        "Client", back_populates="webhook_endpoints"
    )

    # Endpoint configuration
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    url: Mapped[str] = mapped_column(String(2048), nullable=False)

    # Security
    secret: Mapped[str] = mapped_column(String(255), nullable=False)  # For HMAC signing

    # Event subscription
    subscribed_events: Mapped[list] = mapped_column(
        JSON, nullable=False
    )  # List of WebhookEventType

    # Delivery configuration
    max_retry_attempts: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    retry_delay_seconds: Mapped[int] = mapped_column(
        Integer, default=60, nullable=False
    )
    timeout_seconds: Mapped[int] = mapped_column(Integer, default=30, nullable=False)

    # Status and health
    status: Mapped[WebhookStatus] = mapped_column(
        String(30), default=WebhookStatus.PENDING_VERIFICATION, nullable=False
    )
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Failure tracking
    consecutive_failures: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False
    )
    last_success_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_failure_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Rate limiting
    rate_limit_per_minute: Mapped[int | None] = mapped_column(Integer)

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
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Relationships
    webhook_events: Mapped[list["WebhookEvent"]] = relationship(
        "WebhookEvent", back_populates="endpoint", cascade="all, delete-orphan"
    )
    delivery_attempts: Mapped[list["WebhookDeliveryAttempt"]] = relationship(
        "WebhookDeliveryAttempt",
        back_populates="endpoint",
        cascade="all, delete-orphan",
    )

    # Constraints and indexes
    __table_args__ = (
        Index("ix_webhook_endpoints_client_id", "client_id"),
        Index("ix_webhook_endpoints_status", "status"),
        Index("ix_webhook_endpoints_url", "url"),
        UniqueConstraint("client_id", "name", name="uq_client_webhook_name"),
    )


class WebhookEvent(Base):
    """
    Events that need to be delivered to webhook endpoints.
    """

    __tablename__ = "webhook_events"

    id: Mapped[str] = mapped_column(
        PGUUID,
        primary_key=True,
        default=uuid4,
        server_default=text("gen_random_uuid()"),
    )

    # Endpoint association
    endpoint_id: Mapped[str] = mapped_column(
        PGUUID, ForeignKey("webhook_endpoints.id"), nullable=False
    )
    endpoint: Mapped["WebhookEndpoint"] = relationship(
        "WebhookEndpoint", back_populates="webhook_events"
    )

    # Event details
    event_type: Mapped[WebhookEventType] = mapped_column(String(50), nullable=False)
    event_id: Mapped[str] = mapped_column(
        String(255), nullable=False
    )  # Idempotency key

    # Payload
    payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    headers: Mapped[dict | None] = mapped_column(JSON)  # Custom headers to include

    # Delivery tracking
    status: Mapped[WebhookDeliveryStatus] = mapped_column(
        String(20), default=WebhookDeliveryStatus.PENDING, nullable=False
    )
    retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

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
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Error tracking
    last_error: Mapped[str | None] = mapped_column(Text)

    # Relationships
    delivery_attempts: Mapped[list["WebhookDeliveryAttempt"]] = relationship(
        "WebhookDeliveryAttempt", back_populates="event", cascade="all, delete-orphan"
    )

    # Indexes
    __table_args__ = (
        Index("ix_webhook_events_endpoint_id", "endpoint_id"),
        Index("ix_webhook_events_status", "status"),
        Index("ix_webhook_events_event_type", "event_type"),
        Index("ix_webhook_events_created_at", "created_at"),
        Index("ix_webhook_events_scheduled_at", "scheduled_at"),
        UniqueConstraint("endpoint_id", "event_id", name="uq_endpoint_event"),
    )


class WebhookDeliveryAttempt(Base):
    """
    Individual delivery attempts for webhook events.
    """

    __tablename__ = "webhook_delivery_attempts"

    id: Mapped[str] = mapped_column(
        PGUUID,
        primary_key=True,
        default=uuid4,
        server_default=text("gen_random_uuid()"),
    )

    # Event and endpoint association
    event_id: Mapped[str] = mapped_column(
        PGUUID, ForeignKey("webhook_events.id"), nullable=False
    )
    event: Mapped["WebhookEvent"] = relationship(
        "WebhookEvent", back_populates="delivery_attempts"
    )

    endpoint_id: Mapped[str] = mapped_column(
        PGUUID, ForeignKey("webhook_endpoints.id"), nullable=False
    )
    endpoint: Mapped["WebhookEndpoint"] = relationship(
        "WebhookEndpoint", back_populates="delivery_attempts"
    )

    # Attempt details
    attempt_number: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # success, failed, timeout

    # HTTP details
    http_status_code: Mapped[int | None] = mapped_column(Integer)
    request_headers: Mapped[dict | None] = mapped_column(JSON)
    response_headers: Mapped[dict | None] = mapped_column(JSON)
    response_body: Mapped[str | None] = mapped_column(Text)

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
        Index("ix_webhook_delivery_attempts_event_id", "event_id"),
        Index("ix_webhook_delivery_attempts_endpoint_id", "endpoint_id"),
        Index("ix_webhook_delivery_attempts_status", "status"),
        Index("ix_webhook_delivery_attempts_attempted_at", "attempted_at"),
    )


class WebhookLog(Base):
    """
    Aggregated logs for webhook endpoint performance and health monitoring.
    """

    __tablename__ = "webhook_logs"

    id: Mapped[str] = mapped_column(
        PGUUID,
        primary_key=True,
        default=uuid4,
        server_default=text("gen_random_uuid()"),
    )

    # Endpoint association
    endpoint_id: Mapped[str] = mapped_column(
        PGUUID, ForeignKey("webhook_endpoints.id"), nullable=False
    )
    endpoint: Mapped["WebhookEndpoint"] = relationship("WebhookEndpoint")

    # Time period (for aggregated metrics)
    period_start: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    period_end: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    # Aggregated metrics
    total_events: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    successful_deliveries: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False
    )
    failed_deliveries: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    average_response_time_ms: Mapped[int | None] = mapped_column(Integer)

    # Created timestamp
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Indexes
    __table_args__ = (
        Index("ix_webhook_logs_endpoint_id", "endpoint_id"),
        Index("ix_webhook_logs_period", "period_start", "period_end"),
        UniqueConstraint("endpoint_id", "period_start", name="uq_endpoint_period"),
    )
