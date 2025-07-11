from .base import BaseEmailProvider, EmailMessage, ProviderResponse, ProviderStatus
from .email_manager import (
    EmailProviderFactory,
    EmailProviderManager,
)
from .mailgun import MailgunProvider
from .postmark import PostmarkProvider
from .sendgrid import SendGridProvider
from .ses import SESProvider
from .smtp import SMTPProvider

__all__ = [
    # Base classes
    "BaseEmailProvider",
    "EmailMessage",
    "ProviderResponse",
    "ProviderStatus",
    # Provider implementations
    "SMTPProvider",
    "MailgunProvider",
    "SendGridProvider",
    "PostmarkProvider",
    "SESProvider",
    # Management classes
    "EmailProviderFactory",
    "EmailProviderManager",
]
