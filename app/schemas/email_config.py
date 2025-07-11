from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field, model_validator


class EmailProviderType(str, Enum):
    """Email provider types supported by the system."""

    SMTP = "smtp"
    MAILGUN = "mailgun"
    SENDGRID = "sendgrid"
    POSTMARK = "postmark"
    SES = "ses"  # AWS Simple Email Service


# Provider-specific configuration schemas
class SMTPConfig(BaseModel):
    """SMTP provider configuration."""

    provider_type: Literal["smtp"] = "smtp"
    host: str
    port: int = 587
    username: str
    password: str
    use_tls: bool = True
    use_ssl: bool = False


class MailgunConfig(BaseModel):
    """Mailgun provider configuration."""

    provider_type: Literal["mailgun"] = "mailgun"
    api_key: str
    domain: str
    base_url: str = "https://api.mailgun.net/v3"


class SendGridConfig(BaseModel):
    """SendGrid provider configuration."""

    provider_type: Literal["sendgrid"] = "sendgrid"
    api_key: str


class PostmarkConfig(BaseModel):
    """Postmark provider configuration."""

    provider_type: Literal["postmark"] = "postmark"
    server_token: str


class SESConfig(BaseModel):
    """AWS SES provider configuration."""

    provider_type: Literal["ses"] = "ses"
    aws_access_key_id: str
    aws_secret_access_key: str
    region: str = "us-east-1"


# Discriminated union for provider configs
EmailProviderConfig = (
    SMTPConfig | MailgunConfig | SendGridConfig | PostmarkConfig | SESConfig
)


# Client provider configuration (what gets stored in database)
class ClientEmailProvider(BaseModel):
    """Client's email provider configuration - stored in database."""

    provider_config: EmailProviderConfig = Field(..., discriminator="provider_type")

    # Client preferences (not provider limits)
    is_primary: bool = False  # Use for single recipient emails
    is_bulk: bool = True  # Use for bulk emails
    default_from_email: str  # Required fallback sender
    default_from_name: str | None = None

    @model_validator(mode="after")
    def validate_config(self):
        """Validate provider-specific requirements."""
        config = self.provider_config

        # Provider-specific validations
        if config.provider_type == "smtp" and config.port not in [25, 465, 587, 2525]:
            raise ValueError("SMTP port must be 25, 465, 587, or 2525")

        return self


# Simple email sending request (pure relay model)
class EmailSendRequest(BaseModel):
    """Schema for sending emails through the API - pure relay model."""

    to: list[str]  # Recipient email addresses
    subject: str  # Email subject (ready to send)
    content: str  # Email content (ready to send - HTML or plain text)
    content_type: str = "text/html"  # text/html or text/plain
    from_email: str | None = None  # Override default sender
    from_name: str | None = None  # Override default sender name

    class Config:
        json_schema_extra = {
            "example": {
                "to": ["user@example.com"],
                "subject": "Password Reset",
                "content": "<h1>Reset your password</h1><p>Click <a href='...'>here</a></p>",
                "content_type": "text/html",
            }
        }


class EmailSendResponse(BaseModel):
    """Response schema for email sending."""

    notification_id: str
    status: str = "queued"
    message: str = "Email queued for delivery"


# Provider configuration info (read-only)
class EmailProviderInfo(BaseModel):
    """Information about configured email providers."""

    smtp_configured: bool = False
    mailgun_configured: bool = False
    sendgrid_configured: bool = False
    postmark_configured: bool = False
    ses_configured: bool = False
    default_provider: EmailProviderType = EmailProviderType.SMTP


# Utility functions
def is_bulk_send(recipient_count: int) -> bool:
    """Determine if this should be treated as a bulk send.

    Simple rule: 1 recipient = transactional, 2+ recipients = bulk
    """
    return recipient_count > 1


def should_use_bulk_provider(recipient_count: int) -> bool:
    """Alias for is_bulk_send for clarity."""
    return is_bulk_send(recipient_count)
