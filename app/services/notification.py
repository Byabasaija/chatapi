# app/services/notification.py
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import and_, asc, desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.notification import (
    Notification,
    NotificationDeliveryAttempt,
    NotificationStatus,
)
from app.schemas.notification import (
    NotificationCreate,
    NotificationFilter,
    NotificationStats,
    NotificationUpdate,
)
from app.services.base import BaseService


class NotificationService(
    BaseService[Notification, NotificationCreate, NotificationUpdate]
):
    def __init__(self, db: AsyncSession):
        super().__init__(model=Notification, db=db)

    async def create_notification(
        self, *, client_id: UUID, obj_in: NotificationCreate
    ) -> Notification:
        """Create a new notification for a specific client."""
        # Convert Pydantic model to dict for SQLAlchemy
        notification_data = obj_in.model_dump()
        notification_data["client_id"] = str(client_id)

        # Map schema fields to model fields
        if "title" in notification_data:
            notification_data["subject"] = notification_data.pop("title")
        if "scheduled_for" in notification_data:
            notification_data["scheduled_at"] = notification_data.pop("scheduled_for")

        db_obj = self.model(**notification_data)
        self.db.add(db_obj)
        await self.db.commit()
        await self.db.refresh(db_obj)
        return db_obj

    async def get_by_client(
        self, *, client_id: UUID, skip: int = 0, limit: int = 100
    ) -> list[Notification]:
        """Get notifications for a specific client with pagination."""
        result = await self.db.execute(
            select(self.model)
            .where(self.model.client_id == str(client_id))
            .order_by(desc(self.model.created_at))
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def get_with_delivery_attempts(
        self, notification_id: UUID
    ) -> Notification | None:
        """Get notification with its delivery attempts loaded."""
        result = await self.db.execute(
            select(self.model)
            .options(selectinload(self.model.delivery_attempts))
            .where(self.model.id == str(notification_id))
        )
        return result.scalars().first()

    async def get_pending_notifications(self, limit: int = 50) -> list[Notification]:
        """Get pending notifications ready for processing."""
        current_time = datetime.now(timezone.utc)

        result = await self.db.execute(
            select(self.model)
            .where(
                and_(
                    self.model.status == NotificationStatus.PENDING,
                    # Include notifications scheduled for now or past, or not scheduled
                    self.model.scheduled_at.is_(None)
                    | (self.model.scheduled_at <= current_time),
                )
            )
            .order_by(asc(self.model.priority), asc(self.model.created_at))
            .limit(limit)
        )
        return result.scalars().all()

    async def update_status(
        self,
        *,
        notification_id: UUID,
        status: NotificationStatus,
        error_message: str = None,
    ) -> Notification | None:
        """Update notification status and optional error message."""
        notification = await self.get(notification_id)
        if not notification:
            return None

        notification.status = status
        if error_message:
            notification.error_message = error_message
        if status == NotificationStatus.SENT:
            notification.sent_at = datetime.now(timezone.utc)

        await self.db.commit()
        await self.db.refresh(notification)
        return notification

    async def increment_retry_count(self, notification_id: UUID) -> Notification | None:
        """Increment retry count for a notification."""
        notification = await self.get(notification_id)
        if not notification:
            return None

        notification.retry_attempt += 1
        notification.status = NotificationStatus.RETRYING

        await self.db.commit()
        await self.db.refresh(notification)
        return notification

    async def filter_notifications(
        self, *, client_id: UUID, filters: NotificationFilter
    ) -> list[Notification]:
        """Filter notifications based on criteria."""
        query = select(self.model).where(self.model.client_id == str(client_id))

        # Apply filters
        if filters.notification_type:
            query = query.where(
                self.model.notification_type == filters.notification_type
            )

        if filters.status:
            query = query.where(self.model.status == filters.status)

        if filters.priority:
            query = query.where(self.model.priority == filters.priority)

        if filters.date_from:
            query = query.where(self.model.created_at >= filters.date_from)

        if filters.date_to:
            query = query.where(self.model.created_at <= filters.date_to)

        if filters.recipient:
            # Use JSON contains for recipient filtering
            query = query.where(self.model.recipients.contains([filters.recipient]))

        # Apply pagination and ordering
        query = query.order_by(desc(self.model.created_at))
        query = query.offset(filters.offset).limit(filters.limit)

        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_client_stats(
        self, *, client_id: UUID, date_from: datetime, date_to: datetime
    ) -> NotificationStats:
        """Get notification statistics for a client in a date range."""
        # Get counts by status
        result = await self.db.execute(
            select(self.model.status, self.model.notification_type).where(
                and_(
                    self.model.client_id == str(client_id),
                    self.model.created_at >= date_from,
                    self.model.created_at <= date_to,
                )
            )
        )

        notifications = result.fetchall()

        # Initialize counters
        total_sent = total_failed = total_pending = 0
        by_type = {}
        by_status = {}

        for status, notif_type in notifications:
            # Count by status
            by_status[status] = by_status.get(status, 0) + 1

            # Count by type
            by_type[notif_type] = by_type.get(notif_type, 0) + 1

            # Aggregate totals
            if status == NotificationStatus.SENT:
                total_sent += 1
            elif status == NotificationStatus.FAILED:
                total_failed += 1
            elif status in [NotificationStatus.PENDING, NotificationStatus.PROCESSING]:
                total_pending += 1

        # Calculate success rate
        total_processed = total_sent + total_failed
        success_rate = (
            (total_sent / total_processed * 100) if total_processed > 0 else 0.0
        )

        return NotificationStats(
            total_sent=total_sent,
            total_failed=total_failed,
            total_pending=total_pending,
            success_rate=success_rate,
            by_type=by_type,
            by_status=by_status,
            period_start=date_from,
            period_end=date_to,
        )

    async def record_delivery_attempt(
        self,
        *,
        notification_id: UUID,
        attempt_number: int,
        provider_name: str,
        success: bool,
        provider_response: dict = None,
        provider_message_id: str = None,
        error_message: str = None,
        response_time_ms: int = None,
    ) -> NotificationDeliveryAttempt:
        """Record a delivery attempt for a notification."""
        attempt = NotificationDeliveryAttempt(
            notification_id=str(notification_id),
            attempt_number=attempt_number,
            status="success" if success else "failed",
            provider_name=provider_name,
            provider_response=provider_response,
            provider_message_id=provider_message_id,
            error_message=error_message,
            response_time_ms=response_time_ms,
        )

        self.db.add(attempt)
        await self.db.commit()
        await self.db.refresh(attempt)
        return attempt

    async def trigger_delivery(self, notification_id: UUID) -> bool:
        """Trigger async delivery of a notification via Celery task."""
        from app.workers.notification_tasks import process_notification

        # Get the notification with its delivery attempts
        notification = await self.get_with_delivery_attempts(notification_id)
        if not notification:
            return False

        # Prepare notification data for the task
        notification_data = {
            "id": str(notification.id),
            "type": notification.type,
            "client_id": notification.client_id,
            "subject": notification.subject,
            "content": notification.content,
            "metadata": notification.metadata,
            "priority": notification.priority,
            "status": notification.status,
            "scheduled_at": notification.scheduled_at.isoformat()
            if notification.scheduled_at
            else None,
            "to_email": notification.to_email,
            "from_email": notification.from_email,
            "reply_to": notification.reply_to,
            "cc": notification.cc,
            "bcc": notification.bcc,
            "room_id": str(notification.room_id) if notification.room_id else None,
            "email_fallback": notification.email_fallback,
            "attempts": len(notification.delivery_attempts)
            if notification.delivery_attempts
            else 0,
        }

        # Update notification status to processing
        await self.update_status(
            notification_id=notification_id, status=NotificationStatus.PROCESSING
        )

        # Send to Celery
        process_notification.delay(notification_data)
        return True


def get_notification_service(db: AsyncSession) -> NotificationService:
    """Factory function to create NotificationService instance."""
    return NotificationService(db)
