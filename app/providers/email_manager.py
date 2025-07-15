import logging
from typing import Any

from app.schemas.email_config import EmailProviderType

from .base import BaseEmailProvider
from .mailgun import MailgunProvider
from .postmark import PostmarkProvider
from .sendgrid import SendGridProvider
from .ses import SESProvider
from .smtp import SMTPProvider

logger = logging.getLogger(__name__)


class EmailProviderFactory:
    """Factory for creating email providers based on configuration."""

    # Registry of available providers
    _providers = {
        EmailProviderType.SMTP: SMTPProvider,
        EmailProviderType.MAILGUN: MailgunProvider,
        EmailProviderType.SENDGRID: SendGridProvider,
        EmailProviderType.POSTMARK: PostmarkProvider,
        EmailProviderType.SES: SESProvider,
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


class EmailProviderManager:
    """Manages email providers with client-provided configurations."""

    def __init__(self, provider_configs: list[dict] = None):
        """
        Initialize with client-provided provider configurations.

        Args:
            provider_configs: List of provider config dicts like:
            [
                {
                    "provider_type": "smtp",
                    "config": {"host": "smtp.gmail.com", ...},
                    "is_primary": True,
                    "is_bulk": False,
                    "max_recipients": 1,
                    "rate_limit_per_second": 2
                },
                {
                    "provider_type": "sendgrid",
                    "config": {"api_key": "...", ...},
                    "is_primary": False,
                    "is_bulk": True,
                    "max_recipients": 1000,
                    "rate_limit_per_second": 100
                }
            ]
        """
        self.providers: dict[str, BaseEmailProvider] = {}
        self.provider_configs = provider_configs or []
        self._initialized = False

    async def initialize_providers(self):
        """Initialize providers from client configs or system defaults."""
        if self._initialized:
            return

        # Use client configs if provided, otherwise fall back to system defaults
        configs_to_use = self.provider_configs
        if not configs_to_use:
            configs_to_use = EmailProviderFactory.get_default_system_configs()
            logger.info("No client provider configs found, using system defaults")

        if not configs_to_use:
            logger.warning("No provider configurations available (client or system)")
            self._initialized = True
            return

        for config in configs_to_use:
            try:
                provider_type = EmailProviderType(config["provider_type"])
                provider = EmailProviderFactory.create_provider(
                    provider_type, config["config"]
                )

                # Store with metadata
                provider._is_primary = config.get("is_primary", False)
                provider._is_bulk = config.get("is_bulk", True)
                provider._max_recipients = config.get("max_recipients", 100)
                provider._rate_limit_per_second = config.get(
                    "rate_limit_per_second", 10
                )

                # Validate provider configuration
                validation_result = await provider.validate_config()
                if not validation_result.get("valid", False):
                    logger.warning(
                        f"Provider {provider_type} failed validation: "
                        f"{validation_result.get('error', 'Unknown error')}"
                    )
                    continue

                self.providers[config["provider_type"]] = provider
                logger.info(f"Initialized {provider_type} provider successfully")

            except Exception as e:
                logger.error(
                    f"Failed to initialize provider {config.get('provider_type')}: {e}"
                )

        self._initialized = True
        logger.info(
            f"Email provider manager initialized with {len(self.providers)} providers"
        )

    def get_provider_for_sending(
        self, recipient_count: int = 1
    ) -> BaseEmailProvider | None:
        """Get appropriate provider based on recipient count and configuration."""
        if not self.providers:
            logger.warning("No email providers available")
            return None

        # For single/few recipients, prefer primary provider
        if recipient_count <= 5:
            for provider in self.providers.values():
                if getattr(
                    provider, "_is_primary", False
                ) and recipient_count <= getattr(provider, "_max_recipients", 100):
                    return provider

        # For bulk, find suitable bulk provider
        for provider in self.providers.values():
            if getattr(provider, "_is_bulk", True) and recipient_count <= getattr(
                provider, "_max_recipients", 100
            ):
                return provider

        # Fallback to any available provider that can handle the load
        for provider in self.providers.values():
            if recipient_count <= getattr(provider, "_max_recipients", 100):
                return provider

        logger.warning(f"No provider can handle {recipient_count} recipients")
        return None

    def get_fallback_provider(
        self, failed_provider_type: str
    ) -> BaseEmailProvider | None:
        """Get fallback provider when primary fails."""
        for provider_type, provider in self.providers.items():
            if provider_type != failed_provider_type:
                return provider
        return None

    def get_provider_status(self) -> dict[str, Any]:
        """Get status of all providers."""
        status = {
            "initialized": self._initialized,
            "total_providers": len(self.providers),
            "providers": {},
        }

        for provider_type, provider in self.providers.items():
            status["providers"][provider_type] = {
                "is_primary": getattr(provider, "_is_primary", False),
                "is_bulk": getattr(provider, "_is_bulk", True),
                "max_recipients": getattr(provider, "_max_recipients", 100),
                "rate_limit_per_second": getattr(
                    provider, "_rate_limit_per_second", 10
                ),
            }

        return status

    async def validate_all_providers(self) -> dict[str, dict[str, Any]]:
        """Validate configuration of all providers."""
        results = {}
        for provider_type, provider in self.providers.items():
            try:
                results[provider_type] = await provider.validate_config()
            except Exception as e:
                results[provider_type] = {
                    "valid": False,
                    "error": f"Validation exception: {str(e)}",
                }
        return results
