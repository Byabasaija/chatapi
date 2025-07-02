from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class ContentType(str, Enum):
    text = "text"
    image = "image"
    file = "file"
    video = "video"
    audio = "audio"
    document = "document"


# Shared base schema
class MessageBase(BaseModel):
    content: str | None = None
    content_type: ContentType = ContentType.text
    file_url: str | None = None
    file_name: str | None = None
    file_size: int | None = None
    file_mime_type: str | None = None
    reply_to_id: UUID | None = None


# Schema for creating a message
class MessageCreate(MessageBase):
    room_id: UUID
    sender_user_id: str
    sender_display_name: str


# Schema for reading a message (response model)
class MessageRead(MessageBase):
    id: UUID
    room_id: UUID
    sender_user_id: str
    sender_display_name: str
    is_edited: bool
    is_deleted: bool
    created_at: datetime
    updated_at: datetime
    edited_at: datetime | None = None
    reply_to: Optional["MessageRead"] = None
    replies: list["MessageRead"] = []

    model_config = {"from_attributes": True}


# Self-referencing fix (use forward refs)
MessageRead.model_rebuild()


# Schema for updating delivery/read status (optional)
class MessageUpdate(BaseModel):
    is_edited: bool | None = None
    is_deleted: bool | None = None
    edited_at: datetime | None = None

    model_config = {"from_attributes": True}


# Schema for conversation summary
class ConversationSummary(BaseModel):
    partner_id: str
    last_message: MessageRead
    unread_count: int

    model_config = {"from_attributes": True}
