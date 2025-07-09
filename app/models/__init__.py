from .client import Client, ScopedKey, ScopedKeyPermission
from .email_config import ClientEmailConfig, EmailSendingStats, EmailTemplate
from .message import Message
from .notification import (
    Notification,
    NotificationDeliveryAttempt,
    NotificationTemplate,
)
from .room import Room, RoomMembership
from .webhook import WebhookDeliveryAttempt, WebhookEndpoint, WebhookEvent, WebhookLog

__all__ = [
    "Client",
    "Message",
    "Room",
    "RoomMembership",
    "ScopedKey",
    "ScopedKeyPermission",
    "Notification",
    "NotificationDeliveryAttempt",
    "NotificationTemplate",
    "WebhookEndpoint",
    "WebhookEvent",
    "WebhookDeliveryAttempt",
    "WebhookLog",
    "ClientEmailConfig",
    "EmailSendingStats",
    "EmailTemplate",
]
# __all__ is a convention in Python that defines the public interface of a module.
# It specifies which names should be accessible when the module is imported with a wildcard import (e.g., from module import *).
