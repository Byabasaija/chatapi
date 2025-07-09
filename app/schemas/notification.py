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

    notification_type: NotificationType
    title: str = Field(..., max_length=255, description="Notification title")
    content: str = Field(..., description="Notification content/body")
    content_type: str = Field(default="text/plain", description="Content MIME type")
    recipients: list[str] = Field(
        ..., description="List of recipients (emails, user IDs, etc.)"
    )
    priority: NotificationPriority = Field(default=NotificationPriority.NORMAL)
    scheduled_for: datetime | None = Field(
        None, description="Schedule notification for future delivery"
    )
    meta: dict[str, Any] | None = Field(None, description="Additional metadata")
    max_retry_attempts: int = Field(default=3, ge=0, le=10)


class NotificationCreate(NotificationBase):
    """Schema for creating notifications."""

    @validator("recipients")
    def validate_recipients(cls, v, values):
        if not v:
            raise ValueError("At least one recipient is required")

        notification_type = values.get("notification_type")
        if notification_type == NotificationType.EMAIL:
            # For email notifications, validate email format
            for recipient in v:
                if "@" not in recipient:
                    raise ValueError(f"Invalid email format: {recipient}")
        return v

    @validator("content_type")
    def validate_content_type(cls, v):
        allowed_types = ["text/plain", "text/html", "application/json"]
        if v not in allowed_types:
            raise ValueError(f"Content type must be one of: {allowed_types}")
        return v


class NotificationUpdate(BaseModel):
    """Schema for updating notifications."""

    title: str | None = Field(None, max_length=255)
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
