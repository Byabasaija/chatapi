from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel


class ScopedKeyPermission(str, Enum):
    READ_MESSAGES = "read_messages"
    SEND_MESSAGES = "send_messages"
    MANAGE_ROOMS = "manage_rooms"
    INVITE_USERS = "invite_users"


# ======== CLIENT SCHEMAS ========


class ClientBase(BaseModel):
    name: str | None = None


class ClientCreate(ClientBase):
    master_api_key: str


class ClientUpdate(BaseModel):
    name: str | None = None
    is_active: bool | None = None

    model_config = {"from_attributes": True}


class ClientRead(ClientBase):
    id: UUID
    master_api_key: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class APIClientReadWithKey(ClientRead):
    """Returned only once on creation with the key"""

    master_api_key: str

    model_config = {"from_attributes": True}


# ======== SCOPED KEY SCHEMAS ========


class ScopedKeyBase(BaseModel):
    user_id: str
    permissions: list[ScopedKeyPermission]


class ScopedKeyCreate(ScopedKeyBase):
    client_id: UUID
    scoped_api_key: str


class ScopedKeyUpdate(BaseModel):
    permissions: list[ScopedKeyPermission] | None = None
    is_active: bool | None = None

    model_config = {"from_attributes": True}


class ScopedKeyRead(ScopedKeyBase):
    id: UUID
    client_id: UUID
    scoped_api_key: str
    is_active: bool
    last_used_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
