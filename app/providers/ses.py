import logging
from typing import Any

import boto3
from botocore.exceptions import ClientError

from .base import BaseEmailProvider

logger = logging.getLogger(__name__)


class SESProvider(BaseEmailProvider):
    """AWS SES email provider implementation."""

    def __init__(self, config: dict[str, Any]):
        """Initialize SES provider with configuration."""
        super().__init__(config)
        self.aws_access_key_id = config["aws_access_key_id"]
        self.aws_secret_access_key = config["aws_secret_access_key"]
        self.region = config.get("region", "us-east-1")
        self.from_email = config["from_email"]

        # Initialize SES client
        self.client = boto3.client(
            "ses",
            aws_access_key_id=self.aws_access_key_id,
            aws_secret_access_key=self.aws_secret_access_key,
            region_name=self.region,
        )

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
        Send email using AWS SES.

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

            # For bulk sends (>50 recipients), use send_bulk_templated_email
            if len(to_list) > 50:
                return await self._send_bulk(
                    to_list, subject, content, from_email, reply_to, cc, bcc
                )

            # Build destination
            destination = {"ToAddresses": to_list}
            if cc:
                destination["CcAddresses"] = cc
            if bcc:
                destination["BccAddresses"] = bcc

            # Build message
            message = {
                "Subject": {"Data": subject, "Charset": "UTF-8"},
                "Body": {"Html": {"Data": content, "Charset": "UTF-8"}},
            }

            # Prepare send_email parameters
            params = {
                "Source": from_email or self.from_email,
                "Destination": destination,
                "Message": message,
            }

            if reply_to:
                params["ReplyToAddresses"] = [reply_to]

            # Send email
            response = self.client.send_email(**params)

            message_id = response["MessageId"]
            logger.info(f"SES email sent successfully: {message_id}")
            return {
                "success": True,
                "message_id": message_id,
                "provider": "ses",
                "recipients": len(to_list),
            }

        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            error_msg = (
                f"SES ClientError ({error_code}): {e.response['Error']['Message']}"
            )
            logger.error(error_msg)
            return {"success": False, "error": error_msg, "error_code": error_code}
        except Exception as e:
            error_msg = f"SES sending failed: {str(e)}"
            logger.error(error_msg)
            return {"success": False, "error": error_msg}

    async def _send_bulk(
        self,
        to_emails: list[str],
        subject: str,
        content: str,
        from_email: str = None,
        reply_to: str = None,
        cc: list[str] = None,
        bcc: list[str] = None,
    ) -> dict[str, Any]:
        """Send bulk emails using SES in batches."""
        try:
            # SES has a limit of 50 recipients per send_email call
            batch_size = 50
            total_sent = 0
            errors = []

            for i in range(0, len(to_emails), batch_size):
                batch = to_emails[i : i + batch_size]

                try:
                    destination = {"ToAddresses": batch}
                    if cc:
                        destination["CcAddresses"] = cc
                    if bcc:
                        destination["BccAddresses"] = bcc

                    message = {
                        "Subject": {"Data": subject, "Charset": "UTF-8"},
                        "Body": {"Html": {"Data": content, "Charset": "UTF-8"}},
                    }

                    params = {
                        "Source": from_email or self.from_email,
                        "Destination": destination,
                        "Message": message,
                    }

                    if reply_to:
                        params["ReplyToAddresses"] = [reply_to]

                    response = self.client.send_email(**params)
                    total_sent += len(batch)
                    logger.info(
                        f"SES batch sent: {len(batch)} emails, MessageId: {response['MessageId']}"
                    )

                except ClientError as e:
                    error_msg = f"Batch {i//batch_size + 1} failed: {e.response['Error']['Message']}"
                    errors.append(error_msg)
                    logger.error(error_msg)

            success = total_sent > 0
            result = {
                "success": success,
                "provider": "ses",
                "recipients": len(to_emails),
                "successful": total_sent,
            }

            if errors:
                result["errors"] = errors

            return result

        except Exception as e:
            error_msg = f"SES bulk sending failed: {str(e)}"
            logger.error(error_msg)
            return {"success": False, "error": error_msg}

    async def validate_config(self) -> dict[str, Any]:
        """Validate SES configuration."""
        try:
            # Test by getting send quota
            response = self.client.get_send_quota()

            # Check if the from_email is verified
            verified_response = self.client.list_verified_email_addresses()
            verified_emails = verified_response.get("VerifiedEmailAddresses", [])

            if self.from_email not in verified_emails:
                return {
                    "valid": False,
                    "error": f"From email '{self.from_email}' is not verified in SES",
                }

            return {
                "valid": True,
                "provider": "ses",
                "send_quota": response.get("Max24HourSend"),
                "sent_last_24h": response.get("SentLast24Hours"),
            }

        except ClientError as e:
            return {
                "valid": False,
                "error": f"SES validation failed: {e.response['Error']['Message']}",
            }
        except Exception as e:
            return {"valid": False, "error": f"SES validation failed: {str(e)}"}
