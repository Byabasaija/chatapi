from enum import Enum

from pydantic import BaseModel


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

    host: str
    port: int = 587
    username: str
    password: str
    use_tls: bool = True
    use_ssl: bool = False


class MailgunConfig(BaseModel):
    """Mailgun provider configuration."""

    api_key: str
    domain: str
    base_url: str = "https://api.mailgun.net/v3"


class SendGridConfig(BaseModel):
    """SendGrid provider configuration."""

    api_key: str
    from_email: str
    from_name: str | None = None


class PostmarkConfig(BaseModel):
    """Postmark provider configuration."""

    server_token: str
    from_email: str


class SESConfig(BaseModel):
    """AWS SES provider configuration."""

    aws_access_key_id: str
    aws_secret_access_key: str
    region: str = "us-east-1"
    from_email: str


class EmailProviderConfig(BaseModel):
    """Unified email provider configuration."""

    provider_type: EmailProviderType
    config: (SMTPConfig | MailgunConfig | SendGridConfig | PostmarkConfig | SESConfig)

    # Optional settings
    max_recipients: int = 100  # Provider's bulk limit
    rate_limit_per_second: int = 10  # Sending rate limit
    is_primary: bool = False  # Use for single sends
    is_bulk: bool = True  # Use for bulk sends


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
    default_provider: EmailProviderType = EmailProviderType.SMTP
