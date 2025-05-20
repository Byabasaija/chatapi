from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4

from pydantic import model_validator
from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import JSON
from sqlmodel import Field, SQLModel

from app.core.config import settings


class ContentType(str, Enum):
    text = "text"
    image = "image"
    file = "file"
    video = "video"


class Message(SQLModel, table=True):
    """
    Represents a message in the system.
    Attributes:
        id (UUID): Unique identifier for the message.
        client_id (str): ID of the client sending the message.
        sender_id (str): ID of the sender.
        recipient_id (str): ID of the recipient.
        group_id (Optional[str]): ID of the group, if applicable.
        encrypted_payload (Optional[str]): Encrypted message payload for E2EE mode.
        content (Optional[str]): Message content for non-E2EE mode.
        content_type (Optional[str]): Type of content (e.g., "text", "image").
        metadata (Dict): Additional metadata associated with the message.
        created_at (datetime): Timestamp when the message was created.
        delivered (bool): Indicates if the message has been delivered.
        delivered_at (Optional[datetime]): Timestamp when the message was delivered.
    """

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    client_id: str = Field(default=settings.CLIENT_KEY)
    sender_id: str
    recipient_id: str
    group_id: str | None = None

    # For E2EE mode
    encrypted_payload: str | None = None

    # For non-E2EE mode
    content: str | None = None
    content_type: ContentType | None = ContentType.text

    custom_metadata: dict | None = Field(default_factory=dict, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    delivered: bool = False
    delivered_at: datetime | None = None

    @model_validator(mode="after")
    def check_encryption_mode(self) -> "Message":
        if bool(self.content) == bool(self.encrypted_payload):
            raise ValueError(
                "Provide either `content` or `encrypted_payload`, not both or neither."
            )
        return self
