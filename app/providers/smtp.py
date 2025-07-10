import asyncio
import logging
import smtplib
import ssl
import time
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any

from .base import BaseEmailProvider, EmailMessage, ProviderResponse, ProviderStatus

logger = logging.getLogger(__name__)


class SMTPProvider(BaseEmailProvider):
    """SMTP email provider implementation."""

    def __init__(self, config: dict[str, Any]):
        """
        Initialize SMTP provider.

        Expected config:
        {
            "host": "smtp.gmail.com",
            "port": 587,
            "username": "your-email@gmail.com",
            "password": "your-app-password",
            "use_tls": True,
            "use_ssl": False,
            "from_email": "noreply@yourapp.com",
            "from_name": "Your App Name"
        }
        """
        super().__init__(config)
        self.host = config.get("host")
        self.port = config.get("port", 587)
        self.username = config.get("username")
        self.password = config.get("password")
        self.use_tls = config.get("use_tls", True)
        self.use_ssl = config.get("use_ssl", False)
        self.default_from_email = config.get("from_email")
        self.default_from_name = config.get("from_name")

    def is_configured(self) -> bool:
        """Check if SMTP provider has required configuration."""
        required_fields = ["host", "port", "username", "password"]
        return all(self.config.get(field) for field in required_fields)

    async def send_email(self, message: EmailMessage) -> ProviderResponse:
        """Send email via SMTP."""
        start_time = time.time()

        try:
            # Use asyncio to run SMTP in thread pool to avoid blocking
            response = await asyncio.get_event_loop().run_in_executor(
                None, self._send_smtp_email, message
            )

            delivery_time_ms = int((time.time() - start_time) * 1000)
            response.delivery_time_ms = delivery_time_ms

            return response

        except Exception as e:
            logger.error(f"SMTP send failed: {str(e)}")
            delivery_time_ms = int((time.time() - start_time) * 1000)

            return ProviderResponse(
                status=ProviderStatus.FAILED,
                error_message=str(e),
                delivery_time_ms=delivery_time_ms,
            )

    def _send_smtp_email(self, message: EmailMessage) -> ProviderResponse:
        """Internal SMTP sending logic (synchronous)."""
        try:
            # Create message
            msg = MIMEMultipart("alternative")
            msg["From"] = self._format_from_address(message)
            msg["To"] = ", ".join(message.to)
            msg["Subject"] = message.subject

            # Add content
            if message.content_type == "text/html":
                msg.attach(MIMEText(message.content, "html"))
            else:
                msg.attach(MIMEText(message.content, "plain"))

            # Create SMTP connection
            if self.use_ssl:
                server = smtplib.SMTP_SSL(self.host, self.port)
            else:
                server = smtplib.SMTP(self.host, self.port)
                if self.use_tls:
                    server.starttls(context=ssl.create_default_context())

            # Login and send
            server.login(self.username, self.password)
            text = msg.as_string()
            server.sendmail(msg["From"], message.to, text)
            server.quit()

            logger.info(f"SMTP email sent successfully to {message.to}")

            return ProviderResponse(
                status=ProviderStatus.SUCCESS,
                provider_message_id=None,  # SMTP doesn't provide message IDs
                provider_response={"smtp_host": self.host},
            )

        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"SMTP authentication failed: {str(e)}")
            return ProviderResponse(
                status=ProviderStatus.FAILED,
                error_message=f"Authentication failed: {str(e)}",
            )

        except smtplib.SMTPRecipientsRefused as e:
            logger.error(f"SMTP recipients refused: {str(e)}")
            return ProviderResponse(
                status=ProviderStatus.FAILED,
                error_message=f"Recipients refused: {str(e)}",
            )

        except smtplib.SMTPServerDisconnected as e:
            logger.error(f"SMTP server disconnected: {str(e)}")
            return ProviderResponse(
                status=ProviderStatus.RETRY,  # Temporary network issue
                error_message=f"Server disconnected: {str(e)}",
            )

        except Exception as e:
            logger.error(f"SMTP unexpected error: {str(e)}")
            return ProviderResponse(status=ProviderStatus.FAILED, error_message=str(e))

    def _format_from_address(self, message: EmailMessage) -> str:
        """Format the from address with optional name."""
        from_email = message.from_email or self.default_from_email
        from_name = message.from_name or self.default_from_name

        if from_name:
            return f'"{from_name}" <{from_email}>'
        return from_email

    async def verify_configuration(self) -> bool:
        """Verify SMTP configuration by attempting connection."""
        try:
            # Test connection without sending email
            if self.use_ssl:
                server = smtplib.SMTP_SSL(self.host, self.port, timeout=10)
            else:
                server = smtplib.SMTP(self.host, self.port, timeout=10)
                if self.use_tls:
                    server.starttls(context=ssl.create_default_context())

            server.login(self.username, self.password)
            server.quit()

            logger.info(f"SMTP configuration verified for {self.host}")
            return True

        except Exception as e:
            logger.error(f"SMTP configuration verification failed: {str(e)}")
            return False
