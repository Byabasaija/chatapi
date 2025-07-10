import asyncio
import logging
import time
from typing import Any

import aiohttp

from .base import BaseEmailProvider, EmailMessage, ProviderResponse, ProviderStatus

logger = logging.getLogger(__name__)


class MailgunProvider(BaseEmailProvider):
    """Mailgun email provider implementation."""

    def __init__(self, config: dict[str, Any]):
        """
        Initialize Mailgun provider.

        Expected config:
        {
            "api_key": "key-your-mailgun-api-key",
            "domain": "mg.yourdomain.com",
            "base_url": "https://api.mailgun.net/v3",
            "from_email": "noreply@yourdomain.com",
            "from_name": "Your App Name"
        }
        """
        super().__init__(config)
        self.api_key = config.get("api_key")
        self.domain = config.get("domain")
        self.base_url = config.get("base_url", "https://api.mailgun.net/v3")
        self.default_from_email = config.get("from_email")
        self.default_from_name = config.get("from_name")

    def is_configured(self) -> bool:
        """Check if Mailgun provider has required configuration."""
        required_fields = ["api_key", "domain"]
        return all(self.config.get(field) for field in required_fields)

    async def send_email(self, message: EmailMessage) -> ProviderResponse:
        """Send email via Mailgun API."""
        start_time = time.time()

        if not self.is_configured():
            return ProviderResponse(
                status=ProviderStatus.FAILED,
                error_message="Mailgun provider not properly configured",
            )

        try:
            url = f"{self.base_url}/{self.domain}/messages"

            # Prepare form data for Mailgun API
            data = {
                "from": self._format_from_address(message),
                "to": message.to,
                "subject": message.subject,
            }

            # Add content based on type
            if message.content_type == "text/html":
                data["html"] = message.content
            else:
                data["text"] = message.content

            # Optional reply-to
            if message.reply_to:
                data["h:Reply-To"] = message.reply_to

            # Make API request
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url,
                    auth=aiohttp.BasicAuth("api", self.api_key),
                    data=data,
                    timeout=aiohttp.ClientTimeout(total=30),
                ) as response:
                    delivery_time_ms = int((time.time() - start_time) * 1000)
                    response_data = await response.json()

                    if response.status == 200:
                        logger.info(f"Mailgun email sent successfully to {message.to}")

                        return ProviderResponse(
                            status=ProviderStatus.SUCCESS,
                            provider_message_id=response_data.get("id"),
                            provider_response=response_data,
                            delivery_time_ms=delivery_time_ms,
                        )
                    else:
                        logger.error(
                            f"Mailgun API error: {response.status} - {response_data}"
                        )

                        # Determine if we should retry based on status code
                        status = (
                            ProviderStatus.RETRY
                            if response.status >= 500
                            else ProviderStatus.FAILED
                        )

                        return ProviderResponse(
                            status=status,
                            error_message=response_data.get(
                                "message", f"HTTP {response.status}"
                            ),
                            provider_response=response_data,
                            delivery_time_ms=delivery_time_ms,
                        )

        except asyncio.TimeoutError:
            delivery_time_ms = int((time.time() - start_time) * 1000)
            logger.error("Mailgun request timeout")

            return ProviderResponse(
                status=ProviderStatus.RETRY,
                error_message="Request timeout",
                delivery_time_ms=delivery_time_ms,
            )

        except aiohttp.ClientError as e:
            delivery_time_ms = int((time.time() - start_time) * 1000)
            logger.error(f"Mailgun client error: {str(e)}")

            return ProviderResponse(
                status=ProviderStatus.RETRY,
                error_message=f"Client error: {str(e)}",
                delivery_time_ms=delivery_time_ms,
            )

        except Exception as e:
            delivery_time_ms = int((time.time() - start_time) * 1000)
            logger.error(f"Mailgun unexpected error: {str(e)}")

            return ProviderResponse(
                status=ProviderStatus.FAILED,
                error_message=str(e),
                delivery_time_ms=delivery_time_ms,
            )

    def _format_from_address(self, message: EmailMessage) -> str:
        """Format the from address with optional name."""
        from_email = message.from_email or self.default_from_email
        from_name = message.from_name or self.default_from_name

        if from_name:
            return f'"{from_name}" <{from_email}>'
        return from_email

    async def verify_configuration(self) -> bool:
        """Verify Mailgun configuration by checking domain info."""
        if not self.is_configured():
            return False

        try:
            url = f"{self.base_url}/domains/{self.domain}"

            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url,
                    auth=aiohttp.BasicAuth("api", self.api_key),
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as response:
                    if response.status == 200:
                        domain_info = await response.json()
                        domain_status = domain_info.get("domain", {}).get("state", "")

                        logger.info(
                            f"Mailgun domain {self.domain} status: {domain_status}"
                        )
                        return domain_status == "active"
                    else:
                        logger.error(
                            f"Mailgun domain verification failed: {response.status}"
                        )
                        return False

        except Exception as e:
            logger.error(f"Mailgun configuration verification failed: {str(e)}")
            return False
