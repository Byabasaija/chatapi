from datetime import datetime
from enum import Enum
from uuid import uuid4

from sqlalchemy import Boolean, Column, DateTime, String, text
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import validates

from app.core.config import settings
from app.db.base_class import Base


class ContentType(str, Enum):
    text = "text"
    image = "image"
    file = "file"
    video = "video"


class Message(Base):
    __tablename__ = "message"

    id = Column(
        PGUUID,
        primary_key=True,
        default=uuid4,
        server_default=text("gen_random_uuid()"),
    )
    client_id = Column(String, default=settings.CLIENT_KEY, nullable=False)
    sender_id = Column(String, nullable=False)
    recipient_id = Column(String, nullable=False)
    sender_name = Column(String, nullable=True)
    recipient_name = Column(String, nullable=True)
    group_id = Column(String, nullable=True)

    # For E2EE mode
    encrypted_payload = Column(String, nullable=True)

    # For non-E2EE mode
    content = Column(String, nullable=True)
    content_type = Column(String, default=ContentType.text.value, nullable=True)

    custom_metadata = Column(JSON, default=dict, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    delivered = Column(Boolean, default=False, nullable=False)
    delivered_at = Column(DateTime, nullable=True)

    @validates("encrypted_payload", "content")
    def validate_encryption_mode(self, key, value):
        if key == "encrypted_payload" and value and self.content:
            raise ValueError("Cannot provide both 'encrypted_payload' and 'content'")
        elif key == "content" and value and self.encrypted_payload:
            raise ValueError("Cannot provide both 'encrypted_payload' and 'content'")
        return value
