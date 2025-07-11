import logging
from typing import Any

import httpx

from .base import BaseEmailProvider

logger = logging.getLogger(__name__)


class SendGridProvider(BaseEmailProvider):
    """SendGrid email provider implementation."""

    def __init__(self, config: dict[str, Any]):
        """Initialize SendGrid provider with configuration."""
        super().__init__(config)
        self.api_key = config["api_key"]
        self.from_email = config["from_email"]
        self.from_name = config.get("from_name")
        self.base_url = "https://api.sendgrid.com/v3"

    async def send_email(
        self,
        to_email: str | list[str],
        subject: str,
        content: str,
        from_email: str = None,
        reply_to: str = None,
        cc: list[str] = None,
        bcc: list[str] = None,
    ) -> dict[str, Any]:
        """
        Send email using SendGrid API.

        Args:
            to_email: Recipient email(s)
            subject: Email subject
            content: Email content (HTML or plain text)
            from_email: Sender email (optional override)
            reply_to: Reply-to email
            cc: CC recipients
            bcc: BCC recipients

        Returns:
            Dict with success status and details
        """
        try:
            # Prepare recipients
            to_list = [to_email] if isinstance(to_email, str) else to_email

            # Build personalizations
            personalizations = []
            for email in to_list:
                personalizations.append({"to": [{"email": email}]})

            # Add CC/BCC if provided
            if cc:
                for personalization in personalizations:
                    personalization["cc"] = [{"email": email} for email in cc]
            if bcc:
                for personalization in personalizations:
                    personalization["bcc"] = [{"email": email} for email in bcc]

            # Build SendGrid payload
            payload = {
                "personalizations": personalizations,
                "from": {
                    "email": from_email or self.from_email,
                    "name": self.from_name,
                },
                "subject": subject,
                "content": [{"type": "text/html", "value": content}],
            }

            # Add reply-to if specified
            if reply_to:
                payload["reply_to"] = {"email": reply_to}

            # Send via SendGrid API
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/mail/send",
                    json=payload,
                    headers=headers,
                    timeout=30.0,
                )

            if response.status_code == 202:  # SendGrid success code
                logger.info(
                    f"SendGrid email sent successfully to {len(to_list)} recipients"
                )
                return {
                    "success": True,
                    "message_id": response.headers.get("X-Message-Id"),
                    "provider": "sendgrid",
                    "recipients": len(to_list),
                }
            else:
                error_msg = (
                    f"SendGrid API error: {response.status_code} - {response.text}"
                )
                logger.error(error_msg)
                return {
                    "success": False,
                    "error": error_msg,
                    "status_code": response.status_code,
                }

        except Exception as e:
            error_msg = f"SendGrid sending failed: {str(e)}"
            logger.error(error_msg)
            return {"success": False, "error": error_msg}

    async def validate_config(self) -> dict[str, Any]:
        """Validate SendGrid configuration."""
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }

            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/user/profile", headers=headers, timeout=10.0
                )

            if response.status_code == 200:
                return {"valid": True, "provider": "sendgrid"}
            else:
                return {
                    "valid": False,
                    "error": f"Invalid SendGrid API key: {response.status_code}",
                }

        except Exception as e:
            return {"valid": False, "error": f"SendGrid validation failed: {str(e)}"}
