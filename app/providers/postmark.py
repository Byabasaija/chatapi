import logging
from typing import Any

import httpx

from .base import BaseEmailProvider

logger = logging.getLogger(__name__)


class PostmarkProvider(BaseEmailProvider):
    """Postmark email provider implementation."""

    def __init__(self, config: dict[str, Any]):
        """Initialize Postmark provider with configuration."""
        super().__init__(config)
        self.server_token = config["server_token"]
        self.from_email = config["from_email"]
        self.base_url = "https://api.postmarkapp.com"

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
        Send email using Postmark API.

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
            # For bulk sends, use batch API
            if isinstance(to_email, list) and len(to_email) > 1:
                return await self._send_batch(
                    to_email, subject, content, from_email, reply_to, cc, bcc
                )

            # Single email send
            to_addr = to_email[0] if isinstance(to_email, list) else to_email

            payload = {
                "From": from_email or self.from_email,
                "To": to_addr,
                "Subject": subject,
                "HtmlBody": content,
            }

            if reply_to:
                payload["ReplyTo"] = reply_to
            if cc:
                payload["Cc"] = ",".join(cc)
            if bcc:
                payload["Bcc"] = ",".join(bcc)

            headers = {
                "Accept": "application/json",
                "Content-Type": "application/json",
                "X-Postmark-Server-Token": self.server_token,
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/email",
                    json=payload,
                    headers=headers,
                    timeout=30.0,
                )

            if response.status_code == 200:
                result = response.json()
                logger.info(
                    f"Postmark email sent successfully: {result.get('MessageID')}"
                )
                return {
                    "success": True,
                    "message_id": result.get("MessageID"),
                    "provider": "postmark",
                    "recipients": 1,
                }
            else:
                error_msg = (
                    f"Postmark API error: {response.status_code} - {response.text}"
                )
                logger.error(error_msg)
                return {
                    "success": False,
                    "error": error_msg,
                    "status_code": response.status_code,
                }

        except Exception as e:
            error_msg = f"Postmark sending failed: {str(e)}"
            logger.error(error_msg)
            return {"success": False, "error": error_msg}

    async def _send_batch(
        self,
        to_emails: list[str],
        subject: str,
        content: str,
        from_email: str = None,
        reply_to: str = None,
        cc: list[str] = None,
        bcc: list[str] = None,
    ) -> dict[str, Any]:
        """Send batch emails using Postmark batch API."""
        try:
            # Build batch payload
            emails = []
            for email in to_emails:
                email_payload = {
                    "From": from_email or self.from_email,
                    "To": email,
                    "Subject": subject,
                    "HtmlBody": content,
                }
                if reply_to:
                    email_payload["ReplyTo"] = reply_to
                if cc:
                    email_payload["Cc"] = ",".join(cc)
                if bcc:
                    email_payload["Bcc"] = ",".join(bcc)
                emails.append(email_payload)

            headers = {
                "Accept": "application/json",
                "Content-Type": "application/json",
                "X-Postmark-Server-Token": self.server_token,
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/email/batch",
                    json=emails,
                    headers=headers,
                    timeout=60.0,
                )

            if response.status_code == 200:
                results = response.json()
                success_count = sum(1 for r in results if r.get("ErrorCode") == 0)
                logger.info(
                    f"Postmark batch sent: {success_count}/{len(to_emails)} successful"
                )
                return {
                    "success": True,
                    "provider": "postmark",
                    "recipients": len(to_emails),
                    "successful": success_count,
                    "batch_results": results,
                }
            else:
                error_msg = f"Postmark batch API error: {response.status_code} - {response.text}"
                logger.error(error_msg)
                return {
                    "success": False,
                    "error": error_msg,
                    "status_code": response.status_code,
                }

        except Exception as e:
            error_msg = f"Postmark batch sending failed: {str(e)}"
            logger.error(error_msg)
            return {"success": False, "error": error_msg}

    async def validate_config(self) -> dict[str, Any]:
        """Validate Postmark configuration."""
        try:
            headers = {
                "Accept": "application/json",
                "X-Postmark-Server-Token": self.server_token,
            }

            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/server", headers=headers, timeout=10.0
                )

            if response.status_code == 200:
                return {"valid": True, "provider": "postmark"}
            else:
                return {
                    "valid": False,
                    "error": f"Invalid Postmark server token: {response.status_code}",
                }

        except Exception as e:
            return {"valid": False, "error": f"Postmark validation failed: {str(e)}"}
