from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel


class EncryptionMode(str, Enum):
    E2EE = "e2ee"
    NONE = "none"


# Base schema with common attributes
class APIClientBase(BaseModel):
    name: str | None = None
    encryption_mode: EncryptionMode = EncryptionMode.NONE


# Schema for creating an API client
class APIClientCreate(APIClientBase):
    pass


# Schema for reading an API client (response model)
class APIClientRead(APIClientBase):
    id: UUID
    created_at: datetime

    model_config = {
        "from_attributes": True  # Allows conversion from SQLAlchemy model
    }


# Schema for reading an API client with the API key (for initial creation response)
class APIClientReadWithKey(APIClientRead):
    api_key: str

    model_config = {"from_attributes": True}


# Schema for updating an API client (if needed)
class APIClientUpdate(BaseModel):
    name: str | None = None
    encryption_mode: EncryptionMode | None = None

    model_config = {"from_attributes": True}
