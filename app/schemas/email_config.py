from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, SecretStr, validator

from app.models.email_config import EmailProviderType


# Client Email Configuration Schemas
class ClientEmailConfigBase(BaseModel):
    """Base schema for client email configuration."""

    # Provider configuration
    provider_type: EmailProviderType = Field(default=EmailProviderType.SMTP)
    is_active: bool = Field(default=True)
    is_default: bool = Field(
        default=False, description="Whether this is the default config for the client"
    )

    # SMTP Configuration
    smtp_host: str | None = Field(
        None, max_length=255, description="SMTP server hostname"
    )
    smtp_port: int | None = Field(None, ge=1, le=65535, description="SMTP server port")
    smtp_username: str | None = Field(None, max_length=255, description="SMTP username")
    smtp_use_tls: bool | None = Field(True, description="Use TLS encryption")
    smtp_use_ssl: bool | None = Field(False, description="Use SSL encryption")

    # Email metadata
    from_email: EmailStr | None = Field(
        None, description="Default sender email address"
    )
    from_name: str | None = Field(
        None, max_length=255, description="Default sender name"
    )
    reply_to_email: EmailStr | None = Field(
        None, description="Default reply-to address"
    )

    # Rate limiting (per client config)
    rate_limit_per_hour: int | None = Field(
        100, ge=1, description="Max emails per hour"
    )
    rate_limit_per_day: int | None = Field(1000, ge=1, description="Max emails per day")

    # Configuration metadata
    config_name: str | None = Field(
        None, max_length=100, description="Human-readable config name"
    )
    description: str | None = Field(None, description="Configuration description")


class ClientEmailConfigCreate(ClientEmailConfigBase):
    """Schema for creating client email configuration."""

    smtp_password: SecretStr | None = Field(
        None, description="SMTP password (will be encrypted)"
    )

    @validator("smtp_host")
    def validate_smtp_host(cls, v, values):
        provider_type = values.get("provider_type")
        if provider_type == EmailProviderType.SMTP and not v:
            raise ValueError("SMTP host is required for SMTP provider")
        return v

    @validator("smtp_port")
    def validate_smtp_port(cls, v, values):
        provider_type = values.get("provider_type")
        if provider_type == EmailProviderType.SMTP and not v:
            raise ValueError("SMTP port is required for SMTP provider")
        return v

    @validator("smtp_username")
    def validate_smtp_username(cls, v, values):
        provider_type = values.get("provider_type")
        if provider_type == EmailProviderType.SMTP and not v:
            raise ValueError("SMTP username is required for SMTP provider")
        return v

    @validator("from_email")
    def validate_from_email(cls, v, values):
        provider_type = values.get("provider_type")
        if provider_type == EmailProviderType.SMTP and not v:
            raise ValueError("From email is required for SMTP provider")
        return v


class ClientEmailConfigUpdate(BaseModel):
    """Schema for updating client email configuration."""

    is_active: bool | None = None
    is_default: bool | None = None
    smtp_host: str | None = None
    smtp_port: int | None = Field(None, ge=1, le=65535)
    smtp_username: str | None = None
    smtp_password: SecretStr | None = None
    smtp_use_tls: bool | None = None
    smtp_use_ssl: bool | None = None
    from_email: EmailStr | None = None
    from_name: str | None = None
    reply_to_email: EmailStr | None = None
    rate_limit_per_hour: int | None = Field(None, ge=1)
    rate_limit_per_day: int | None = Field(None, ge=1)
    config_name: str | None = None
    description: str | None = None


class ClientEmailConfigRead(ClientEmailConfigBase):
    """Schema for reading client email configuration."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    client_id: UUID
    created_at: datetime
    updated_at: datetime
    last_used_at: datetime | None = None

    # Don't expose the password in read operations
    smtp_password: str | None = Field(None, exclude=True)


# Email Sending Statistics Schemas
class EmailSendingStatsBase(BaseModel):
    """Base schema for email sending statistics."""

    date: datetime = Field(..., description="Statistics date")
    emails_sent: int = Field(default=0, ge=0, description="Total emails sent")
    emails_failed: int = Field(default=0, ge=0, description="Total emails failed")
    emails_bounced: int = Field(default=0, ge=0, description="Total emails bounced")
    smtp_sent: int = Field(default=0, ge=0, description="Emails sent via SMTP")
    mailgun_sent: int = Field(default=0, ge=0, description="Emails sent via Mailgun")


class EmailSendingStatsCreate(EmailSendingStatsBase):
    """Schema for creating email sending statistics."""

    client_id: UUID


class EmailSendingStatsRead(EmailSendingStatsBase):
    """Schema for reading email sending statistics."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    client_id: UUID
    created_at: datetime
    updated_at: datetime


# Email Template Schemas
class EmailTemplateBase(BaseModel):
    """Base schema for email templates."""

    template_name: str = Field(..., max_length=100, description="Template identifier")
    template_type: str = Field(
        ..., description="Template type (transactional, marketing, system)"
    )
    subject: str = Field(..., description="Email subject template")
    html_content: str | None = Field(None, description="HTML email content")
    text_content: str | None = Field(None, description="Plain text email content")
    is_active: bool = Field(default=True)
    variables: dict[str, str] | None = Field(
        None, description="Available template variables"
    )


class EmailTemplateCreate(EmailTemplateBase):
    """Schema for creating email templates."""

    @validator("template_type")
    def validate_template_type(cls, v):
        allowed_types = ["transactional", "marketing", "system"]
        if v not in allowed_types:
            raise ValueError(f"Template type must be one of: {allowed_types}")
        return v

    @validator("html_content", "text_content")
    def validate_content(cls, v, values, field):
        html_content = values.get("html_content") if field.name == "text_content" else v
        text_content = values.get("text_content") if field.name == "html_content" else v  # noqa

        if field.name == "text_content" and not html_content and not v:
            raise ValueError("Either html_content or text_content must be provided")

        return v


class EmailTemplateUpdate(BaseModel):
    """Schema for updating email templates."""

    template_name: str | None = Field(None, max_length=100)
    template_type: str | None = None
    subject: str | None = None
    html_content: str | None = None
    text_content: str | None = None
    is_active: bool | None = None
    variables: dict[str, str] | None = None


class EmailTemplateRead(EmailTemplateBase):
    """Schema for reading email templates."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    client_id: UUID
    version: int = 1
    usage_count: int = 0
    last_used_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


# Email Sending Schemas
class EmailSendRequest(BaseModel):
    """Schema for sending emails through the API."""

    to: list[EmailStr] = Field(..., description="Recipient email addresses")
    subject: str = Field(..., description="Email subject")
    html_content: str | None = Field(None, description="HTML email content")
    text_content: str | None = Field(None, description="Plain text email content")
    from_email: EmailStr | None = Field(
        None, description="Sender email (overrides config)"
    )
    from_name: str | None = Field(None, description="Sender name (overrides config)")
    reply_to: EmailStr | None = Field(
        None, description="Reply-to address (overrides config)"
    )
    template_id: int | None = Field(None, description="Use template instead of content")
    template_variables: dict[str, Any] | None = Field(
        None, description="Variables for template"
    )
    priority: str = Field(
        default="normal", description="Email priority (low, normal, high)"
    )
    scheduled_for: datetime | None = Field(
        None, description="Schedule email for future delivery"
    )

    @validator("to")
    def validate_recipients(cls, v):
        if not v:
            raise ValueError("At least one recipient is required")
        if len(v) > 100:
            raise ValueError("Maximum 100 recipients per email")
        return v

    @validator("priority")
    def validate_priority(cls, v):
        allowed_priorities = ["low", "normal", "high"]
        if v not in allowed_priorities:
            raise ValueError(f"Priority must be one of: {allowed_priorities}")
        return v


class EmailSendResponse(BaseModel):
    """Response schema for email sending."""

    id: UUID
    status: str = "queued"
    message: str = "Email queued for delivery"
    provider_used: str | None = None


# Batch Email Operations
class EmailBatchSendRequest(BaseModel):
    """Schema for batch email sending."""

    emails: list[EmailSendRequest] = Field(..., max_items=50)

    @validator("emails")
    def validate_batch_size(cls, v):
        if len(v) == 0:
            raise ValueError("At least one email is required")
        if len(v) > 50:
            raise ValueError("Maximum 50 emails per batch")
        return v


class EmailBatchResponse(BaseModel):
    """Response schema for batch email operations."""

    total: int
    successful: int
    failed: int
    email_ids: list[UUID]
    errors: list[str] | None = None


# Configuration Testing
class EmailConfigTestRequest(BaseModel):
    """Schema for testing email configuration."""

    config_id: int
    test_email: EmailStr = Field(..., description="Email address to send test email to")


class EmailConfigTestResponse(BaseModel):
    """Response schema for email configuration testing."""

    success: bool
    message: str
    error_details: str | None = None
    response_time_ms: int | None = None


# Statistics and Analytics
class EmailClientStats(BaseModel):
    """Schema for client email statistics."""

    total_sent: int = 0
    total_failed: int = 0
    total_bounced: int = 0
    success_rate: float = Field(0.0, ge=0.0, le=100.0)
    smtp_sent: int = 0
    mailgun_sent: int = 0
    daily_limit_remaining: int = 0
    hourly_limit_remaining: int = 0
    period_start: datetime
    period_end: datetime


# Provider Configuration
class MailgunConfigRead(BaseModel):
    """Schema for reading Mailgun configuration (system-wide)."""

    is_configured: bool = False
    domain: str | None = None
    base_url: str | None = None
    daily_limit: int | None = None


class SMTPProviderInfo(BaseModel):
    """Schema for SMTP provider information."""

    provider_name: str
    smtp_host: str
    smtp_port: int
    supports_tls: bool = True
    supports_ssl: bool = False
    common_settings: dict[str, Any] = Field(default_factory=dict)
