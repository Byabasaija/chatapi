# app/api/api_v1/routes/notification.py
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel

from app.api.deps import AuthClientDep, NotificationServiceDep
from app.schemas.notification import (
    NotificationCreate,
    NotificationFilter,
    NotificationPriority,
    NotificationRead,
    NotificationStats,
    NotificationStatus,
    NotificationType,
    NotificationUpdate,
)

router = APIRouter()


# Request/Response models for better API documentation
class SendNotificationRequest(BaseModel):
    type: NotificationType
    subject: str
    content: str
    priority: NotificationPriority = NotificationPriority.normal
    metadata: dict = {}
    scheduled_for: str | None = None  # ISO datetime string

    # Email-specific fields
    to_email: str | None = None
    from_email: str | None = None
    reply_to: str | None = None
    cc: list[str] | None = None
    bcc: list[str] | None = None

    # WebSocket-specific fields
    room_id: UUID | None = None

    # Email fallback for WebSocket notifications
    email_fallback: dict | None = (
        None  # {"to_email": "user@example.com", "subject": "..."}
    )


class NotificationResponse(BaseModel):
    success: bool
    message: str
    data: dict | None = None


# ==================== CORE NOTIFICATION OPERATIONS ====================


@router.post("/", response_model=NotificationRead, summary="Send a notification")
async def send_notification(
    request: SendNotificationRequest,
    auth_client: AuthClientDep,
    notification_service: NotificationServiceDep,
):
    """
    Send a new notification.

    Supports email and WebSocket notifications with appropriate metadata.
    """
    try:
        client, scoped_key = auth_client

        # Create notification object
        notification_data = NotificationCreate(
            type=request.type,
            subject=request.subject,
            content=request.content,
            priority=request.priority,
            metadata=request.metadata,
            scheduled_for=request.scheduled_for,
            to_email=request.to_email,
            from_email=request.from_email,
            reply_to=request.reply_to,
            cc=request.cc,
            bcc=request.bcc,
            room_id=request.room_id,
            email_fallback=request.email_fallback,
        )

        # Create the notification
        notification = await notification_service.create_notification(
            client_id=client.id, obj_in=notification_data
        )

        # Trigger async delivery
        await notification_service.trigger_delivery(notification.id)

        return notification

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send notification: {str(e)}",
        )


@router.get("/", response_model=list[NotificationRead], summary="List notifications")
async def list_notifications(
    auth_client: AuthClientDep,
    notification_service: NotificationServiceDep,
    limit: int = Query(default=50, le=100, ge=1),
    offset: int = Query(default=0, ge=0),
    type: NotificationType | None = Query(default=None),
    status: NotificationStatus | None = Query(default=None),
    priority: NotificationPriority | None = Query(default=None),
    from_date: str | None = Query(default=None, description="ISO datetime string"),
    to_date: str | None = Query(default=None, description="ISO datetime string"),
):
    """
    List notifications for the authenticated client with optional filtering.
    """
    try:
        client, scoped_key = auth_client

        # Build filter
        filter_params = NotificationFilter(
            type=type,
            status=status,
            priority=priority,
            from_date=from_date,
            to_date=to_date,
        )

        notifications = await notification_service.get_by_client(
            client_id=client.id, filter_params=filter_params, limit=limit, offset=offset
        )

        return notifications

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list notifications: {str(e)}",
        )


@router.get(
    "/{notification_id}",
    response_model=NotificationRead,
    summary="Get notification by ID",
)
async def get_notification(
    notification_id: UUID,
    auth_client: AuthClientDep,
    notification_service: NotificationServiceDep,
):
    """
    Get a specific notification by ID.
    """
    try:
        client, scoped_key = auth_client

        notification = await notification_service.get_by_id_and_client(
            notification_id=notification_id, client_id=client.id
        )

        if not notification:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found"
            )

        return notification

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get notification: {str(e)}",
        )


@router.put(
    "/{notification_id}", response_model=NotificationRead, summary="Update notification"
)
async def update_notification(
    notification_id: UUID,
    request: NotificationUpdate,
    auth_client: AuthClientDep,
    notification_service: NotificationServiceDep,
):
    """
    Update a notification (only allowed for pending/scheduled notifications).
    """
    try:
        client, scoped_key = auth_client

        # Get existing notification
        notification = await notification_service.get_by_id_and_client(
            notification_id=notification_id, client_id=client.id
        )

        if not notification:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found"
            )

        # Only allow updates for pending/scheduled notifications
        if notification.status not in [
            NotificationStatus.pending,
            NotificationStatus.scheduled,
        ]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only pending or scheduled notifications can be updated",
            )

        # Update the notification
        updated_notification = await notification_service.update(
            db_obj=notification, obj_in=request
        )

        return updated_notification

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update notification: {str(e)}",
        )


@router.delete(
    "/{notification_id}",
    response_model=NotificationResponse,
    summary="Cancel notification",
)
async def cancel_notification(
    notification_id: UUID,
    auth_client: AuthClientDep,
    notification_service: NotificationServiceDep,
):
    """
    Cancel a notification (only allowed for pending/scheduled notifications).
    """
    try:
        client, scoped_key = auth_client

        # Get existing notification
        notification = await notification_service.get_by_id_and_client(
            notification_id=notification_id, client_id=client.id
        )

        if not notification:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found"
            )

        # Only allow cancellation for pending/scheduled notifications
        if notification.status not in [
            NotificationStatus.pending,
            NotificationStatus.scheduled,
        ]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only pending or scheduled notifications can be cancelled",
            )

        # Cancel the notification
        await notification_service.cancel_notification(notification_id)

        return NotificationResponse(
            success=True, message="Notification cancelled successfully"
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cancel notification: {str(e)}",
        )


@router.post(
    "/{notification_id}/retry",
    response_model=NotificationResponse,
    summary="Retry failed notification",
)
async def retry_notification(
    notification_id: UUID,
    auth_client: AuthClientDep,
    notification_service: NotificationServiceDep,
):
    """
    Retry a failed notification delivery.
    """
    try:
        client, scoped_key = auth_client

        # Get existing notification
        notification = await notification_service.get_by_id_and_client(
            notification_id=notification_id, client_id=client.id
        )

        if not notification:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found"
            )

        # Only allow retry for failed notifications
        if notification.status != NotificationStatus.failed:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only failed notifications can be retried",
            )

        # Retry the notification
        await notification_service.retry_notification(notification_id)

        return NotificationResponse(
            success=True, message="Notification retry triggered successfully"
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retry notification: {str(e)}",
        )


@router.get(
    "/stats", response_model=NotificationStats, summary="Get notification statistics"
)
async def get_notification_stats(
    auth_client: AuthClientDep,
    notification_service: NotificationServiceDep,
    days: int = Query(default=30, ge=1, le=365),
):
    """
    Get notification statistics for the authenticated client.
    """
    try:
        client, scoped_key = auth_client

        stats = await notification_service.get_stats(client_id=client.id, days=days)

        return stats

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get notification stats: {str(e)}",
        )
