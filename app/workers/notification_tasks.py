# app/workers/notification_tasks.py
# ruff: noqa
"""
Notification processing tasks for Celery background processing.
Handles email sending, WebSocket notifications, and multi-channel delivery.
"""
import asyncio
import logging
from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.celery_app import celery_app
from app.core.db import async_session_maker
from app.models.notification import NotificationStatus
from app.providers.email_manager import (
    EmailProviderManager,
    EmailProviderConfig,
    EmailProviderType,
)
from app.services.notification import get_notification_service

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, name="app.workers.notification_tasks.process_notification")
def process_notification(self, notification_data: dict[str, Any]) -> dict[str, Any]:
    """
    Process a notification event and dispatch to appropriate channels.

    Args:
        notification_data: Notification payload from webhook or API

    Returns:
        Processing result with delivery status
    """
    try:
        notification_id = notification_data.get("id", "unknown")
        notification_type = notification_data.get("type", "unknown")
        logger.info(
            f"Processing notification: {notification_id} of type {notification_type}"
        )

        # Run the async processing in an event loop
        loop = asyncio.get_event_loop()
        result = loop.run_until_complete(process_notification_async(notification_data))

        return result
    except Exception as e:
        logger.error(f"Notification processing failed: {str(e)}")

        # Update notification status to failed
        try:
            notification_id = notification_data.get("id")
            if notification_id:
                loop = asyncio.get_event_loop()
                loop.run_until_complete(
                    update_notification_status(
                        UUID(notification_id), NotificationStatus.FAILED, str(e)
                    )
                )
        except Exception as status_error:
            logger.error(f"Failed to update notification status: {str(status_error)}")

        raise


async def process_notification_async(
    notification_data: dict[str, Any],
) -> dict[str, Any]:
    """Async implementation of notification processing."""
    notification_id = notification_data.get("id")
    notification_type = notification_data.get("type")

    # Get notification service
    async with async_session_maker() as session:
        notification_service = get_notification_service(session)

        try:
            # Route to appropriate handler based on notification type
            result = None

            if notification_type == "email":
                result = await process_email_notification(notification_data, session)
            elif notification_type == "websocket":
                result = await process_websocket_notification(
                    notification_data, session
                )
            else:
                error_msg = f"Unsupported notification type: {notification_type}"
                logger.error(error_msg)
                await notification_service.update_status(
                    notification_id=UUID(notification_id),
                    status=NotificationStatus.FAILED,
                    error_message=error_msg,
                )
                return {"status": "error", "error": error_msg}

            # Update notification status based on result
            if result and result.get("status") == "success":
                await notification_service.update_status(
                    notification_id=UUID(notification_id),
                    status=NotificationStatus.SENT,
                )
                return {
                    "status": "success",
                    "notification_id": notification_id,
                    "delivery_info": result,
                    "timestamp": datetime.utcnow().isoformat(),
                }
            else:
                error_msg = result.get("error", "Unknown delivery error")
                await notification_service.update_status(
                    notification_id=UUID(notification_id),
                    status=NotificationStatus.FAILED,
                    error_message=error_msg,
                )
                return {
                    "status": "error",
                    "notification_id": notification_id,
                    "error": error_msg,
                }

        except Exception as e:
            error_msg = f"Notification processing error: {str(e)}"
            logger.error(error_msg)
            await notification_service.update_status(
                notification_id=UUID(notification_id),
                status=NotificationStatus.FAILED,
                error_message=error_msg,
            )
            return {"status": "error", "error": error_msg}


async def update_notification_status(
    notification_id: UUID, status: NotificationStatus, error_message: str = None
):
    """Update notification status in the database."""
    async with async_session_maker() as session:
        notification_service = get_notification_service(session)
        await notification_service.update_status(
            notification_id=notification_id, status=status, error_message=error_message
        )


async def process_email_notification(
    notification_data: dict[str, Any], session: AsyncSession
) -> dict[str, Any]:
    """Process an email notification."""
    try:
        # Extract email data
        notification_id = notification_data.get("id")
        to_email = notification_data.get("to_email")
        subject = notification_data.get("subject")
        content = notification_data.get("content")

        # Validate required fields
        if not all([to_email, subject, content]):
            return {
                "status": "error",
                "error": "Missing required email fields (to_email, subject, content)",
            }

        # Prepare email data
        email_data = {
            "to": to_email,
            "subject": subject,
            "content": content,
            "from_email": notification_data.get("from_email"),
            "reply_to": notification_data.get("reply_to"),
            "cc": notification_data.get("cc", []),
            "bcc": notification_data.get("bcc", []),
            "metadata": notification_data.get("metadata", {}),
        }

        # Create recipient count to determine provider
        recipient_count = 1
        if email_data.get("cc"):
            recipient_count += len(email_data["cc"])
        if email_data.get("bcc"):
            recipient_count += len(email_data["bcc"])

        # Initialize email provider manager
        provider_manager = EmailProviderManager()
        await provider_manager.initialize_providers()

        # Get appropriate provider
        provider = provider_manager.get_provider_for_sending(recipient_count)
        if not provider:
            return {"status": "error", "error": "No email provider available"}

        # Send email
        provider_name = provider.__class__.__name__
        start_time = datetime.utcnow()
        send_result = await provider.send_email(
            to_email=email_data["to"],
            subject=email_data["subject"],
            content=email_data["content"],
            from_email=email_data.get("from_email"),
            reply_to=email_data.get("reply_to"),
            cc=email_data.get("cc"),
            bcc=email_data.get("bcc"),
        )
        end_time = datetime.utcnow()
        response_time_ms = int((end_time - start_time).total_seconds() * 1000)

        # Record delivery attempt
        notification_service = get_notification_service(session)
        await notification_service.record_delivery_attempt(
            notification_id=UUID(notification_id),
            attempt_number=notification_data.get("attempts", 0) + 1,
            provider_name=provider_name,
            success=send_result.get("success", False),
            provider_response=send_result,
            provider_message_id=send_result.get("message_id"),
            error_message=send_result.get("error"),
            response_time_ms=response_time_ms,
        )

        if send_result.get("success", False):
            return {
                "status": "success",
                "provider": provider_name,
                "message_id": send_result.get("message_id"),
                "timestamp": datetime.utcnow().isoformat(),
            }
        else:
            # Try fallback if available
            provider_type = (
                EmailProviderType.SMTP
                if provider_name == "SMTPProvider"
                else EmailProviderType.MAILGUN
            )
            fallback = provider_manager.get_fallback_provider(provider_type)

            if fallback:
                logger.info(
                    f"Primary provider failed, trying fallback: {fallback.__class__.__name__}"
                )
                start_time = datetime.utcnow()
                fallback_result = await fallback.send_email(
                    to_email=email_data["to"],
                    subject=email_data["subject"],
                    content=email_data["content"],
                    from_email=email_data.get("from_email"),
                    reply_to=email_data.get("reply_to"),
                    cc=email_data.get("cc"),
                    bcc=email_data.get("bcc"),
                )
                end_time = datetime.utcnow()
                response_time_ms = int((end_time - start_time).total_seconds() * 1000)

                # Record fallback attempt
                await notification_service.record_delivery_attempt(
                    notification_id=UUID(notification_id),
                    attempt_number=notification_data.get("attempts", 0) + 2,
                    provider_name=fallback.__class__.__name__,
                    success=fallback_result.get("success", False),
                    provider_response=fallback_result,
                    provider_message_id=fallback_result.get("message_id"),
                    error_message=fallback_result.get("error"),
                    response_time_ms=response_time_ms,
                )

                if fallback_result.get("success", False):
                    return {
                        "status": "success",
                        "provider": fallback.__class__.__name__,
                        "message_id": fallback_result.get("message_id"),
                        "fallback_used": True,
                        "timestamp": datetime.utcnow().isoformat(),
                    }

            # Both primary and fallback failed (or no fallback)
            return {
                "status": "error",
                "error": send_result.get("error", "Email delivery failed"),
                "provider": provider_name,
            }

    except Exception as e:
        logger.error(f"Email processing error: {str(e)}")
        return {"status": "error", "error": str(e)}


async def process_websocket_notification(
    notification_data: dict[str, Any], session: AsyncSession
) -> dict[str, Any]:
    """Process a WebSocket notification."""
    try:
        # Extract WebSocket data
        notification_id = notification_data.get("id")
        room_id = notification_data.get("room_id")
        target_client_id = notification_data.get("target_client_id")
        content = notification_data.get("content")
        subject = notification_data.get("subject")
        metadata = notification_data.get("metadata", {})

        # Validate required fields
        if not content:
            return {
                "status": "error",
                "error": "Missing required content for WebSocket notification",
            }

        if not (room_id or target_client_id):
            return {
                "status": "error",
                "error": "WebSocket notification requires either room_id or target_client_id",
            }

        # Import the WebSocket utility here to avoid circular imports
        from app.sockets.notification_utils import send_websocket_notification

        # Convert UUID strings to UUID objects if needed
        uuid_room_id = UUID(room_id) if room_id else None
        uuid_target_client_id = UUID(target_client_id) if target_client_id else None

        # Send the WebSocket notification
        ws_result = await send_websocket_notification(
            content=content,
            subject=subject,
            metadata=metadata,
            room_id=uuid_room_id,
            target_client_id=uuid_target_client_id,
        )

        # Record delivery attempt
        notification_service = get_notification_service(session)
        success = ws_result.get("success", False)

        await notification_service.record_delivery_attempt(
            notification_id=UUID(notification_id),
            attempt_number=notification_data.get("attempts", 0) + 1,
            provider_name="WebSocketManager",
            success=success,
            provider_response=ws_result,
            provider_message_id=f"ws-{datetime.utcnow().timestamp()}",
            error_message=", ".join(ws_result.get("errors", []))
            if not success
            else None,
            response_time_ms=10,  # WebSocket delivery is typically fast
        )

        if success:
            return {
                "status": "success",
                "target": f"room:{room_id}"
                if room_id
                else f"client:{target_client_id}",
                "delivered_to": ws_result.get("delivered_to", []),
                "timestamp": datetime.utcnow().isoformat(),
            }
        else:
            return {
                "status": "error",
                "error": ", ".join(
                    ws_result.get("errors", ["Unknown WebSocket delivery error"])
                ),
                "timestamp": datetime.utcnow().isoformat(),
            }

    except Exception as e:
        logger.error(f"WebSocket processing error: {str(e)}")
        return {"status": "error", "error": str(e)}
