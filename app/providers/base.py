from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any


class ProviderStatus(str, Enum):
    """Provider delivery status."""

    SUCCESS = "success"
    FAILED = "failed"
    RETRY = "retry"


@dataclass
class EmailMessage:
    """Standardized email message format for providers."""

    to: list[str]
    subject: str
    content: str
    content_type: str = "text/html"
    from_email: str | None = None
    from_name: str | None = None
    reply_to: str | None = None


@dataclass
class ProviderResponse:
    """Standardized response from email providers."""

    status: ProviderStatus
    provider_message_id: str | None = None
    error_message: str | None = None
    provider_response: dict[str, Any] | None = None
    delivery_time_ms: int | None = None


class BaseEmailProvider(ABC):
    """Abstract base class for email providers."""

    def __init__(self, config: dict[str, Any]):
        """Initialize provider with configuration."""
        self.config = config
        self.provider_name = self.__class__.__name__.lower().replace("provider", "")

    @abstractmethod
    async def send_email(self, message: EmailMessage) -> ProviderResponse:
        """
        Send an email message.

        Args:
            message: EmailMessage object with all email details

        Returns:
            ProviderResponse with delivery status and details
        """
        pass

    @abstractmethod
    async def verify_configuration(self) -> bool:
        """
        Verify that the provider is properly configured.

        Returns:
            True if configuration is valid and provider is reachable
        """
        pass

    def get_provider_name(self) -> str:
        """Get the provider name."""
        return self.provider_name

    def is_configured(self) -> bool:
        """Check if provider has minimum required configuration."""
        return bool(self.config)
