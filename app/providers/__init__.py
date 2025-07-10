from .base import BaseEmailProvider, EmailMessage, ProviderResponse, ProviderStatus
from .email_manager import (
    EmailProviderConfig,
    EmailProviderFactory,
    EmailProviderManager,
)
from .mailgun import MailgunProvider
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
    # Management classes
    "EmailProviderFactory",
    "EmailProviderConfig",
    "EmailProviderManager",
]
