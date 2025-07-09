from pydantic import BaseModel

from app.models.email_config import EmailProviderType


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
