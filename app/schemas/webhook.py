from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, validator

from app.models.webhook import WebhookEventType, WebhookStatus


# Webhook Endpoint Schemas
class WebhookEndpointBase(BaseModel):
    """Base schema for webhook endpoints."""

    url: HttpUrl = Field(..., description="Webhook endpoint URL")
    event_types: list[WebhookEventType] = Field(
        ..., description="Events to subscribe to"
    )
    description: str | None = Field(None, max_length=500)
    is_active: bool = Field(default=True)

    # Security and configuration
    secret: str | None = Field(
        None, description="Secret for webhook signature verification"
    )
    timeout_seconds: int = Field(default=30, ge=1, le=300)
    max_retry_attempts: int = Field(default=3, ge=0, le=10)

    # Custom headers for the webhook
    custom_headers: dict[str, str] | None = Field(
        None, description="Custom headers to send"
    )


class WebhookEndpointCreate(WebhookEndpointBase):
    """Schema for creating webhook endpoints."""

    @validator("event_types")
    def validate_event_types(cls, v):
        if not v:
            raise ValueError("At least one event type is required")
        if len(set(v)) != len(v):
            raise ValueError("Duplicate event types are not allowed")
        return v

    @validator("custom_headers")
    def validate_custom_headers(cls, v):
        if v:
            # Prevent setting sensitive headers
            forbidden_headers = {
                "authorization",
                "host",
                "user-agent",
                "content-length",
            }
            for header in v.keys():
                if header.lower() in forbidden_headers:
                    raise ValueError(f"Header '{header}' is not allowed")
        return v


class WebhookEndpointUpdate(BaseModel):
    """Schema for updating webhook endpoints."""

    url: HttpUrl | None = None
    event_types: list[WebhookEventType] | None = None
    description: str | None = None
    is_active: bool | None = None
    secret: str | None = None
    timeout_seconds: int | None = Field(None, ge=1, le=300)
    max_retry_attempts: int | None = Field(None, ge=0, le=10)
    custom_headers: dict[str, str] | None = None


class WebhookEndpointRead(WebhookEndpointBase):
    """Schema for reading webhook endpoints."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    client_id: UUID
    created_at: datetime
    updated_at: datetime
    last_triggered_at: datetime | None = None
    total_deliveries: int = 0
    successful_deliveries: int = 0
    failed_deliveries: int = 0

    # Don't expose the secret in read operations
    secret: str | None = Field(None, exclude=True)


# Webhook Event Schemas
class WebhookEventBase(BaseModel):
    """Base schema for webhook events."""

    event_type: WebhookEventType
    event_data: dict[str, Any] = Field(..., description="Event payload data")
    resource_id: str | None = Field(
        None, description="ID of the resource that triggered the event"
    )
    idempotency_key: str | None = Field(
        None, description="Client-provided idempotency key"
    )


class WebhookEventCreate(WebhookEventBase):
    """Schema for creating webhook events."""

    @validator("event_data")
    def validate_event_data(cls, v):
        if not v:
            raise ValueError("Event data cannot be empty")
        return v


class WebhookEventRead(WebhookEventBase):
    """Schema for reading webhook events."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    client_id: UUID
    status: WebhookStatus
    created_at: datetime
    processed_at: datetime | None = None
    retry_count: int = 0
    last_error: str | None = None


# Webhook Delivery Attempt Schemas
class WebhookDeliveryAttemptBase(BaseModel):
    """Base schema for webhook delivery attempts."""

    http_status_code: int | None = Field(None, ge=100, le=599)
    response_body: str | None = Field(None, max_length=10000)
    response_headers: dict[str, str] | None = None
    error_message: str | None = None
    delivery_duration_ms: int | None = Field(None, ge=0)


class WebhookDeliveryAttemptCreate(WebhookDeliveryAttemptBase):
    """Schema for creating delivery attempts."""

    webhook_event_id: UUID
    webhook_endpoint_id: UUID
    attempt_number: int = Field(..., ge=1)
    success: bool


class WebhookDeliveryAttemptRead(WebhookDeliveryAttemptBase):
    """Schema for reading delivery attempts."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    webhook_event_id: UUID
    webhook_endpoint_id: UUID
    attempt_number: int
    success: bool
    attempted_at: datetime


# Webhook Log Schemas
class WebhookLogBase(BaseModel):
    """Base schema for webhook logs."""

    log_level: str = Field(..., description="Log level (INFO, WARN, ERROR)")
    message: str = Field(..., description="Log message")
    details: dict[str, Any] | None = Field(None, description="Additional log details")


class WebhookLogCreate(WebhookLogBase):
    """Schema for creating webhook logs."""

    client_id: UUID
    webhook_endpoint_id: UUID | None = None
    webhook_event_id: UUID | None = None


class WebhookLogRead(WebhookLogBase):
    """Schema for reading webhook logs."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    client_id: UUID
    webhook_endpoint_id: UUID | None = None
    webhook_event_id: UUID | None = None
    created_at: datetime


# Response Schemas
class WebhookEventResponse(BaseModel):
    """Response schema for webhook event creation."""

    id: UUID
    status: WebhookStatus
    message: str = "Webhook event queued successfully"
    endpoints_notified: int = 0


class WebhookTestResponse(BaseModel):
    """Response schema for webhook testing."""

    success: bool
    status_code: int | None = None
    response_time_ms: int | None = None
    error_message: str | None = None


# Statistics and Analytics
class WebhookEndpointStats(BaseModel):
    """Schema for webhook endpoint statistics."""

    endpoint_id: UUID
    total_events: int = 0
    successful_deliveries: int = 0
    failed_deliveries: int = 0
    success_rate: float = Field(0.0, ge=0.0, le=100.0)
    avg_response_time_ms: float | None = None
    last_success_at: datetime | None = None
    last_failure_at: datetime | None = None


class WebhookClientStats(BaseModel):
    """Schema for client webhook statistics."""

    total_endpoints: int = 0
    active_endpoints: int = 0
    total_events: int = 0
    successful_deliveries: int = 0
    failed_deliveries: int = 0
    success_rate: float = Field(0.0, ge=0.0, le=100.0)
    by_event_type: dict[str, int] = Field(default_factory=dict)
    period_start: datetime
    period_end: datetime


# Filtering and Search
class WebhookEventFilter(BaseModel):
    """Schema for filtering webhook events."""

    event_type: WebhookEventType | None = None
    status: WebhookStatus | None = None
    date_from: datetime | None = None
    date_to: datetime | None = None
    resource_id: str | None = None
    limit: int = Field(default=50, ge=1, le=1000)
    offset: int = Field(default=0, ge=0)


class WebhookEndpointFilter(BaseModel):
    """Schema for filtering webhook endpoints."""

    is_active: bool | None = None
    event_type: WebhookEventType | None = None
    limit: int = Field(default=50, ge=1, le=1000)
    offset: int = Field(default=0, ge=0)


# Batch Operations
class WebhookEventBatch(BaseModel):
    """Schema for batch webhook event creation."""

    events: list[WebhookEventCreate] = Field(..., max_items=50)

    @validator("events")
    def validate_batch_size(cls, v):
        if len(v) == 0:
            raise ValueError("At least one event is required")
        if len(v) > 50:
            raise ValueError("Maximum 50 events per batch")
        return v


class WebhookBatchResponse(BaseModel):
    """Response schema for batch webhook operations."""

    total: int
    successful: int
    failed: int
    event_ids: list[UUID]
    errors: list[str] | None = None
