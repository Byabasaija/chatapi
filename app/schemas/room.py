from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel

# ===== ENUMS =====


class RoomType(str, Enum):
    direct = "direct"
    group = "group"
    channel = "channel"


class MemberRole(str, Enum):
    owner = "owner"
    admin = "admin"
    member = "member"


# ===== ROOM SCHEMAS =====


class RoomBase(BaseModel):
    name: str | None = None
    description: str | None = None
    room_type: RoomType = RoomType.group
    max_members: int | None = 100


class RoomCreate(RoomBase):
    client_id: UUID
    created_by_user_id: str


class RoomUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    room_type: RoomType | None = None
    is_active: bool | None = None
    max_members: int | None = None

    model_config = {"from_attributes": True}


class RoomRead(RoomBase):
    id: UUID
    client_id: UUID
    created_by_user_id: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    last_message_at: datetime | None = None

    model_config = {"from_attributes": True}


# ===== ROOM MEMBERSHIP SCHEMAS =====


class RoomMembershipBase(BaseModel):
    user_id: str
    display_name: str
    role: MemberRole = MemberRole.member


class RoomMembershipCreate(RoomMembershipBase):
    room_id: UUID


class RoomMembershipUpdate(BaseModel):
    display_name: str | None = None
    role: MemberRole | None = None
    left_at: datetime | None = None
    is_active: bool | None = None
    last_read_message_id: UUID | None = None
    last_read_at: datetime | None = None

    model_config = {"from_attributes": True}


class RoomMembershipRead(RoomMembershipBase):
    id: UUID
    room_id: UUID
    joined_at: datetime
    left_at: datetime | None = None
    is_active: bool
    last_read_message_id: UUID | None = None
    last_read_at: datetime | None = None

    model_config = {"from_attributes": True}


# ===== API RESPONSE SCHEMAS =====


class RoomResponseBase(BaseModel):
    """Base response model for room operations"""

    success: bool
    message: str


class RoomResponse(RoomResponseBase):
    """Standard room operation response with optional data"""

    data: dict | None = None


class RoomMemberResponse(RoomResponseBase):
    """Response for member operations"""

    member_data: RoomMembershipRead | None = None


class RoomListResponse(RoomResponseBase):
    """Response for room list operations"""

    rooms: list[RoomRead] = []
    total_count: int = 0


# ===== SPECIALIZED REQUEST SCHEMAS =====


class RoomJoinRequest(BaseModel):
    """Request to join a room (for public rooms or invitations)"""

    display_name: str
    invitation_code: str | None = None


class RoomInviteRequest(BaseModel):
    """Request to invite users to a room"""

    user_ids: list[str]
    role: MemberRole = MemberRole.member
    message: str | None = None


class RoomSearchRequest(BaseModel):
    """Request for searching rooms"""

    query: str
    room_type: RoomType | None = None
    limit: int = 20
    offset: int = 0


# ===== EXTENDED READ SCHEMAS =====


class RoomReadWithMembers(RoomRead):
    """Room details with member list included"""

    memberships: list[RoomMembershipRead] = []
    member_count: int = 0


class RoomSummary(RoomBase):
    """Lightweight room summary for lists"""

    id: UUID
    member_count: int
    last_message_at: datetime | None = None
    unread_count: int = 0  # For the current user

    model_config = {"from_attributes": True}
