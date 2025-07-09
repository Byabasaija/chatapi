import os

from celery import Celery

# Redis as broker and result backend
broker_url = os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0")
result_backend = os.getenv("CELERY_RESULT_BACKEND", "redis://redis:6379/0")

celery_app = Celery(
    "chatapi_worker",
    broker=broker_url,
    backend=result_backend,
    include=[
        "app.workers.room_tasks",
        "app.workers.notification_tasks",
        "app.workers.webhook_tasks",
        "app.workers.utility_tasks",
        "app.workers.test",
    ],
)

# Configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_routes={
        # Room management tasks
        "app.workers.room_tasks.cleanup_inactive_rooms": {"queue": "maintenance"},
        "app.workers.room_tasks.generate_room_statistics": {"queue": "analytics"},
        # Notification tasks
        "app.workers.notification_tasks.process_notification": {
            "queue": "notifications"
        },
        "app.workers.notification_tasks.send_email": {"queue": "email"},
        "app.workers.notification_tasks.send_bulk_email": {"queue": "bulk_email"},
        "app.workers.notification_tasks.send_websocket_notification": {
            "queue": "websocket"
        },
        "app.workers.notification_tasks.send_webhook_notification": {
            "queue": "webhook"
        },
        # Webhook processing tasks
        "app.workers.webhook_tasks.process_webhook_event": {"queue": "webhook"},
        "app.workers.webhook_tasks.retry_failed_webhook": {"queue": "webhook"},
        "app.workers.webhook_tasks.validate_webhook_endpoint": {"queue": "webhook"},
        # Utility tasks
        "app.workers.utility_tasks.health_check": {"queue": "monitoring"},
        "app.workers.utility_tasks.cleanup_old_notifications": {"queue": "maintenance"},
        "app.workers.utility_tasks.cleanup_old_logs": {"queue": "maintenance"},
        "app.workers.utility_tasks.generate_system_report": {"queue": "analytics"},
        "app.workers.utility_tasks.monitor_queue_health": {"queue": "monitoring"},
    },
    task_default_queue="default",
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    worker_max_tasks_per_child=1000,
)

# Periodic tasks (Celery Beat)
celery_app.conf.beat_schedule = {
    "cleanup-inactive-rooms": {
        "task": "app.workers.room_tasks.cleanup_inactive_rooms",
        "schedule": 86400.0,  # Daily (24 hours)
    },
    "cleanup-old-notifications": {
        "task": "app.workers.utility_tasks.cleanup_old_notifications",
        "schedule": 604800.0,  # Weekly (7 days)
    },
    "cleanup-old-logs": {
        "task": "app.workers.utility_tasks.cleanup_old_logs",
        "schedule": 2592000.0,  # Monthly (30 days)
    },
    "generate-system-report": {
        "task": "app.workers.utility_tasks.generate_system_report",
        "schedule": 3600.0,  # Hourly
    },
    "monitor-queue-health": {
        "task": "app.workers.utility_tasks.monitor_queue_health",
        "schedule": 300.0,  # Every 5 minutes
    },
}
