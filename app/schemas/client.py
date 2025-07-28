from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel


class ScopedKeyPermission(str, Enum):
    READ_MESSAGES = "read_messages"
    SEND_MESSAGES = "send_messages"
    MANAGE_ROOMS = "manage_rooms"
    INVITE_USERS = "invite_users"
    JOIN_ROOMS = "join_rooms"


# ======== CLIENT SCHEMAS ========


class ClientBase(BaseModel):
    name: str | None = None


class ClientCreate(ClientBase):
    pass


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
    pass


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


class ScopedKeyReadWithKey(ScopedKeyRead):
    """Returned only once on creation with the key"""

    scoped_api_key: str

    model_config = {"from_attributes": True}


# ======== USER AUTHENTICATION SCHEMAS ========


class UserLoginRequest(BaseModel):
    """Request schema for user login/authentication"""

    user_id: str
    display_name: str | None = None
    permissions: list[ScopedKeyPermission] = [
        ScopedKeyPermission.READ_MESSAGES,
        ScopedKeyPermission.SEND_MESSAGES,
    ]


class UserLoginResponse(BaseModel):
    """Response schema for user login - always returns a fresh API key"""

    user_id: str
    display_name: str
    api_key: str  # Always a new key that replaces any previous key
    permissions: list[ScopedKeyPermission]


class UserKeyResetRequest(BaseModel):
    """Request schema for resetting a user's API key"""

    user_id: str
    reason: str | None = None  # Optional reason for auditing


class UserKeyResetResponse(BaseModel):
    """Response schema for key reset"""

    user_id: str
    api_key: str
    permissions: list[ScopedKeyPermission]
    message: str
