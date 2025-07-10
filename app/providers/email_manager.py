import logging
import os
from typing import Any

from app.schemas.email_config import EmailProviderType

from .base import BaseEmailProvider
from .mailgun import MailgunProvider
from .smtp import SMTPProvider

logger = logging.getLogger(__name__)


class EmailProviderFactory:
    """Factory for creating email providers based on configuration."""

    # Registry of available providers
    _providers = {
        EmailProviderType.SMTP: SMTPProvider,
        EmailProviderType.MAILGUN: MailgunProvider,
    }

    @classmethod
    def create_provider(
        cls, provider_type: EmailProviderType, config: dict[str, Any]
    ) -> BaseEmailProvider:
        """
        Create an email provider instance.

        Args:
            provider_type: Type of provider to create
            config: Provider-specific configuration

        Returns:
            Configured provider instance

        Raises:
            ValueError: If provider type is not supported
        """
        if provider_type not in cls._providers:
            raise ValueError(f"Unsupported provider type: {provider_type}")

        provider_class = cls._providers[provider_type]
        return provider_class(config)

    @classmethod
    def get_available_providers(cls) -> list[EmailProviderType]:
        """Get list of available provider types."""
        return list(cls._providers.keys())

    @classmethod
    def register_provider(cls, provider_type: EmailProviderType, provider_class: type):
        """Register a new provider type (for extensibility)."""
        cls._providers[provider_type] = provider_class


class EmailProviderConfig:
    """Manages email provider configuration from environment variables."""

    @staticmethod
    def get_smtp_config() -> dict[str, Any]:
        """Get SMTP configuration from environment variables."""
        return {
            "host": os.getenv("SMTP_HOST"),
            "port": int(os.getenv("SMTP_PORT", "587")),
            "username": os.getenv("SMTP_USERNAME"),
            "password": os.getenv("SMTP_PASSWORD"),
            "use_tls": os.getenv("SMTP_USE_TLS", "true").lower() == "true",
            "use_ssl": os.getenv("SMTP_USE_SSL", "false").lower() == "true",
            "from_email": os.getenv("SMTP_FROM_EMAIL"),
            "from_name": os.getenv("SMTP_FROM_NAME"),
        }

    @staticmethod
    def get_mailgun_config() -> dict[str, Any]:
        """Get Mailgun configuration from environment variables."""
        return {
            "api_key": os.getenv("MAILGUN_API_KEY"),
            "domain": os.getenv("MAILGUN_DOMAIN"),
            "base_url": os.getenv("MAILGUN_BASE_URL", "https://api.mailgun.net/v3"),
            "from_email": os.getenv("MAILGUN_FROM_EMAIL"),
            "from_name": os.getenv("MAILGUN_FROM_NAME"),
        }

    @staticmethod
    def get_provider_config(provider_type: EmailProviderType) -> dict[str, Any]:
        """Get configuration for specific provider type."""
        if provider_type == EmailProviderType.SMTP:
            return EmailProviderConfig.get_smtp_config()
        elif provider_type == EmailProviderType.MAILGUN:
            return EmailProviderConfig.get_mailgun_config()
        else:
            raise ValueError(f"Unknown provider type: {provider_type}")


class EmailProviderManager:
    """Manages multiple email providers and handles routing logic."""

    def __init__(self):
        self.providers: dict[EmailProviderType, BaseEmailProvider] = {}
        self.primary_provider: EmailProviderType | None = None
        self.fallback_provider: EmailProviderType | None = None

    async def initialize_providers(self):
        """Initialize all configured providers."""
        # Try to initialize SMTP provider
        try:
            smtp_config = EmailProviderConfig.get_smtp_config()
            smtp_provider = EmailProviderFactory.create_provider(
                EmailProviderType.SMTP, smtp_config
            )

            if smtp_provider.is_configured():
                if await smtp_provider.verify_configuration():
                    self.providers[EmailProviderType.SMTP] = smtp_provider
                    if not self.primary_provider:
                        self.primary_provider = EmailProviderType.SMTP
                    logger.info("SMTP provider initialized successfully")
                else:
                    logger.warning("SMTP provider configuration verification failed")
            else:
                logger.info("SMTP provider not configured")

        except Exception as e:
            logger.error(f"Failed to initialize SMTP provider: {str(e)}")

        # Try to initialize Mailgun provider
        try:
            mailgun_config = EmailProviderConfig.get_mailgun_config()
            mailgun_provider = EmailProviderFactory.create_provider(
                EmailProviderType.MAILGUN, mailgun_config
            )

            if mailgun_provider.is_configured():
                if await mailgun_provider.verify_configuration():
                    self.providers[EmailProviderType.MAILGUN] = mailgun_provider
                    # Mailgun is preferred for bulk/reliability
                    self.primary_provider = EmailProviderType.MAILGUN
                    if EmailProviderType.SMTP in self.providers:
                        self.fallback_provider = EmailProviderType.SMTP
                    logger.info("Mailgun provider initialized successfully")
                else:
                    logger.warning("Mailgun provider configuration verification failed")
            else:
                logger.info("Mailgun provider not configured")

        except Exception as e:
            logger.error(f"Failed to initialize Mailgun provider: {str(e)}")

        if not self.providers:
            logger.error("No email providers could be initialized!")
            raise RuntimeError("No email providers available")

        logger.info(f"Email providers initialized: {list(self.providers.keys())}")
        logger.info(
            f"Primary provider: {self.primary_provider}, Fallback: {self.fallback_provider}"
        )

    def get_provider_for_sending(
        self, recipient_count: int = 1
    ) -> BaseEmailProvider | None:
        """
        Get the best provider for sending based on routing logic.

        Args:
            recipient_count: Number of recipients (for bulk vs transactional routing)

        Returns:
            Best available provider or None if no providers available
        """
        # Simple routing logic:
        # - Use Mailgun for bulk sends (>10 recipients) if available
        # - Use primary provider for normal sends
        # - Fall back to secondary if primary fails

        if recipient_count > 10 and EmailProviderType.MAILGUN in self.providers:
            return self.providers[EmailProviderType.MAILGUN]

        if self.primary_provider and self.primary_provider in self.providers:
            return self.providers[self.primary_provider]

        # Return any available provider
        if self.providers:
            return next(iter(self.providers.values()))

        return None

    def get_fallback_provider(
        self, failed_provider_type: EmailProviderType
    ) -> BaseEmailProvider | None:
        """Get fallback provider when primary fails."""
        for provider_type, provider in self.providers.items():
            if provider_type != failed_provider_type:
                return provider
        return None

    def get_provider_status(self) -> dict[str, Any]:
        """Get status of all providers."""
        return {
            "providers": list(self.providers.keys()),
            "primary": self.primary_provider,
            "fallback": self.fallback_provider,
            "total_providers": len(self.providers),
        }
