from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, validator

from app.models.notification import (
    NotificationPriority,
    NotificationStatus,
    NotificationType,
)


# Base Schemas
class NotificationBase(BaseModel):
    """Base schema for notifications."""

    type: NotificationType
    subject: str = Field(..., max_length=255, description="Notification subject")
    content: str = Field(..., description="Notification content/body")
    priority: NotificationPriority = Field(default=NotificationPriority.NORMAL)
    meta: dict[str, Any] | None = Field(None, description="Additional metadata")
    scheduled_for: datetime | None = Field(
        None, description="Schedule notification for future delivery"
    )

    # Email-specific fields
    to_email: str | None = None
    from_email: str | None = None
    reply_to: str | None = None
    cc: list[str] | None = None
    bcc: list[str] | None = None

    # WebSocket-specific fields
    room_id: UUID | None = None

    # Email fallback for WebSocket notifications
    email_fallback: dict[str, Any] | None = None

    # Optional provider configuration for this specific notification
    # If not provided, client's stored provider configs will be used
    provider_config: dict[str, Any] | None = Field(
        None, description="Optional email provider config for this notification"
    )

    max_retry_attempts: int = Field(default=3, ge=0, le=10)


class NotificationCreate(NotificationBase):
    """Schema for creating notifications."""

    @validator("to_email")
    def validate_email(cls, v):
        if v and "@" not in v:
            raise ValueError(f"Invalid email format: {v}")
        return v

    @validator("type")
    def validate_notification_fields(cls, v, values):
        if v == NotificationType.EMAIL:
            to_email = values.get("to_email")
            if not to_email:
                raise ValueError("to_email is required for email notifications")
        elif v == NotificationType.WEBSOCKET:
            room_id = values.get("room_id")
            email_fallback = values.get("email_fallback")
            # WebSocket notifications need either room_id OR email_fallback
            if not room_id and not email_fallback:
                raise ValueError(
                    "WebSocket notifications require either room_id or email_fallback"
                )
        return v


class NotificationUpdate(BaseModel):
    """Schema for updating notifications."""

    subject: str | None = Field(None, max_length=255)
    content: str | None = None
    priority: NotificationPriority | None = None
    scheduled_for: datetime | None = None
    meta: dict[str, Any] | None = None
    max_retry_attempts: int | None = Field(None, ge=0, le=10)


class NotificationRead(NotificationBase):
    """Schema for reading notifications."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    client_id: UUID
    status: NotificationStatus
    sent_at: datetime | None = None
    error_message: str | None = None
    retry_count: int = 0
    created_at: datetime
    updated_at: datetime


class NotificationResponse(BaseModel):
    """API response schema for notification operations."""

    id: UUID
    status: NotificationStatus
    message: str = "Notification queued successfully"


# Delivery Attempt Schemas
class NotificationDeliveryAttemptBase(BaseModel):
    """Base schema for delivery attempts."""

    provider_used: str = Field(..., description="Provider used for delivery")
    provider_response: dict[str, Any] | None = Field(
        None, description="Provider response data"
    )
    error_message: str | None = None
    delivery_duration_ms: int | None = Field(None, ge=0)


class NotificationDeliveryAttemptCreate(NotificationDeliveryAttemptBase):
    """Schema for creating delivery attempts."""

    notification_id: UUID
    attempt_number: int = Field(..., ge=1)
    success: bool


class NotificationDeliveryAttemptRead(NotificationDeliveryAttemptBase):
    """Schema for reading delivery attempts."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    notification_id: UUID
    attempt_number: int
    success: bool
    attempted_at: datetime


# Batch Operations
class NotificationBatchCreate(BaseModel):
    """Schema for batch notification creation."""

    notifications: list[NotificationCreate] = Field(..., max_items=100)

    @validator("notifications")
    def validate_batch_size(cls, v):
        if len(v) == 0:
            raise ValueError("At least one notification is required")
        if len(v) > 100:
            raise ValueError("Maximum 100 notifications per batch")
        return v


class NotificationBatchResponse(BaseModel):
    """Response schema for batch operations."""

    total: int
    successful: int
    failed: int
    notification_ids: list[UUID]
    errors: list[str] | None = None


# Statistics and Analytics
class NotificationStats(BaseModel):
    """Schema for notification statistics."""

    total_sent: int = 0
    total_failed: int = 0
    total_pending: int = 0
    success_rate: float = Field(0.0, ge=0.0, le=100.0)
    avg_delivery_time_ms: float | None = None
    by_type: dict[str, int] = Field(default_factory=dict)
    by_status: dict[str, int] = Field(default_factory=dict)
    period_start: datetime
    period_end: datetime


# Search and Filtering
class NotificationFilter(BaseModel):
    """Schema for filtering notifications."""

    notification_type: NotificationType | None = None
    status: NotificationStatus | None = None
    priority: NotificationPriority | None = None
    date_from: datetime | None = None
    date_to: datetime | None = None
    recipient: str | None = None
    limit: int = Field(default=50, ge=1, le=1000)
    offset: int = Field(default=0, ge=0)
