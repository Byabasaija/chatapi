# app/workers/__init__.py
"""
Celery worker tasks organized by domain.
All tasks are imported here to ensure they're discoverable by Celery.
"""

# Import all task modules to register them with Celery

# Export commonly used tasks for easier importing
from .notification_tasks import (
    process_notification,
    send_bulk_email,
    send_email,
    send_webhook_notification,
    send_websocket_notification,
)
from .room_tasks import cleanup_inactive_rooms, generate_room_statistics
from .test import test_celery
from .utility_tasks import (
    cleanup_old_logs,
    cleanup_old_notifications,
    generate_system_report,
    health_check,
    monitor_queue_health,
)
from .webhook_tasks import (
    process_webhook_event,
    retry_failed_webhook,
    validate_webhook_endpoint,
)

__all__ = [
    # Room tasks
    "cleanup_inactive_rooms",
    "generate_room_statistics",
    # Notification tasks
    "process_notification",
    "send_email",
    "send_bulk_email",
    "send_websocket_notification",
    "send_webhook_notification",
    # Webhook tasks
    "process_webhook_event",
    "retry_failed_webhook",
    "validate_webhook_endpoint",
    # Utility tasks
    "health_check",
    "cleanup_old_notifications",
    "cleanup_old_logs",
    "generate_system_report",
    "monitor_queue_health",
    # Test task
    "test_celery",
]
