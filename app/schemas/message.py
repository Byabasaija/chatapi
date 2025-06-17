# app/schemas/message.py
from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, field_validator


class ContentType(str, Enum):
    text = "text"
    image = "image"
    file = "file"
    video = "video"


# Base schema with common attributes
class MessageBase(BaseModel):
    sender_id: str
    recipient_id: str
    sender_name: str | None = None
    recipient_name: str | None = None
    group_id: str | None = None
    content_type: ContentType | None = ContentType.text
    read_status: bool | None = None
    read_at: datetime | None = None


# Schema for creating a message
class MessageCreate(MessageBase):
    encrypted_payload: str | None = None
    content: str | None = None

    @field_validator("*")
    def check_encryption_mode(cls, v, info):
        values = info.data
        if "encrypted_payload" in values and "content" in values:
            if bool(values.get("content")) == bool(values.get("encrypted_payload")):
                raise ValueError(
                    "Provide either `content` or `encrypted_payload`, not both or neither."
                )
        return v


# Schema for reading a message (response model)
class MessageRead(MessageCreate):
    id: UUID
    client_id: str
    created_at: datetime
    delivered: bool
    delivered_at: datetime | None = None

    model_config = {
        "from_attributes": True  # Allows conversion from SQLAlchemy model
    }


# Schema for updating a message
class MessageUpdate(BaseModel):
    delivered: bool | None = None
    delivered_at: datetime | None = None
    read_status: bool | None = None
    read_at: datetime | None = None

    model_config = {
        "from_attributes": True  # Allows conversion from SQLAlchemy model
    }


# Additional schema for conversation summary
class ConversationSummary(BaseModel):
    """Schema for conversation summary"""

    partner_id: str
    last_message: MessageRead
    unread_count: int

    model_config = {"from_attributes": True}
