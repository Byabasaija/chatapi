# app/api/api_v1/routes/room.py

from uuid import UUID

from fastapi import APIRouter, HTTPException, Path, Query, status

from app.api.deps import AuthClientDep, RoomServiceDep
from app.schemas.room import (
    MemberRole,
    RoomBase,
    RoomCreate,
    RoomMembershipBase,
    RoomMembershipRead,
    RoomRead,
    RoomResponse,
    RoomUpdate,
)

router = APIRouter()


# ==================== ROOM MANAGEMENT ====================


@router.post("/", response_model=RoomRead, summary="Create a new room")
async def create_room(
    request: RoomBase,
    auth_client: AuthClientDep,
    room_service: RoomServiceDep,
):
    """
    Create a new room (group chat, channel, etc.).

    The authenticated user becomes the owner of the room.
    Different room types have different behaviors:
    - `direct`: 1-on-1 chat (max 2 members)
    - `group`: Group chat with multiple members
    - `channel`: Public channel for broadcasts
    """
    try:
        client, scoped_key = auth_client
        creator_user_id = scoped_key.user_id if scoped_key else str(client.id)
        creator_display_name = (
            scoped_key.user_id if scoped_key else (client.name or "API Client")
        )

        room_data = RoomCreate(
            client_id=client.id,
            created_by_user_id=creator_user_id,
            name=request.name,
            description=request.description,
            room_type=request.room_type,
            max_members=request.max_members,
        )

        room = await room_service.create_room(
            client_id=client.id,
            creator_user_id=creator_user_id,
            creator_display_name=creator_display_name,
            room_data=room_data,
        )

        return room
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create room: {str(e)}",
        )


@router.get("/", response_model=list[RoomRead], summary="Get user's rooms")
async def get_user_rooms(
    auth_client: AuthClientDep,
    room_service: RoomServiceDep,
):
    """
    Get all rooms the authenticated user is a member of.

    Returns rooms where the user has an active membership.
    """
    try:
        client, scoped_key = auth_client
        user_id = scoped_key.user_id if scoped_key else str(client.id)

        rooms = await room_service.get_user_rooms(
            user_id=user_id,
            client_id=client.id,
        )

        return rooms
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve rooms: {str(e)}",
        )


@router.get("/{room_id}", response_model=RoomRead, summary="Get room details")
async def get_room(
    room_id: UUID = Path(..., description="Room ID to retrieve"),
    auth_client: AuthClientDep = None,
    room_service: RoomServiceDep = None,
    include_members: bool = Query(
        False, description="Include room members in response"
    ),
):
    """
    Get detailed information about a specific room.

    Optionally includes all room members if `include_members=true`.
    Only accessible to room members.
    """
    try:
        client, scoped_key = auth_client
        user_id = scoped_key.user_id if scoped_key else str(client.id)

        # Check if user can access this room
        can_access = await room_service.user_can_access_room(room_id, user_id)
        if not can_access:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have access to this room",
            )

        if include_members:
            room = await room_service.get_room_with_members(room_id)
        else:
            room = await room_service.get(room_id)

        if not room:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Room not found",
            )

        return room
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve room: {str(e)}",
        )


@router.put("/{room_id}", response_model=RoomRead, summary="Update room")
async def update_room(
    room_id: UUID = Path(..., description="Room ID to update"),
    room_update: RoomUpdate = None,
    auth_client: AuthClientDep = None,
    room_service: RoomServiceDep = None,
):
    """
    Update room details (name, description, etc.).

    Only room owners and admins can update room details.
    """
    try:
        client, scoped_key = auth_client
        user_id = scoped_key.user_id if scoped_key else str(client.id)

        # Check user's role in room
        user_role = await room_service.get_member_role(room_id, user_id)
        if not user_role or user_role not in [MemberRole.owner, MemberRole.admin]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only room owners and admins can update room details",
            )

        room = await room_service.update(id=room_id, obj_in=room_update)
        if not room:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Room not found",
            )

        return room
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update room: {str(e)}",
        )


# ==================== MEMBER MANAGEMENT ====================


@router.get(
    "/{room_id}/members",
    response_model=list[RoomMembershipRead],
    summary="Get room members",
)
async def get_room_members(
    room_id: UUID = Path(..., description="Room ID to get members from"),
    auth_client: AuthClientDep = None,
    room_service: RoomServiceDep = None,
):
    """
    Get all active members of a room.

    Only accessible to room members.
    """
    try:
        client, scoped_key = auth_client
        user_id = scoped_key.user_id if scoped_key else str(client.id)

        # Check if user can access this room
        can_access = await room_service.user_can_access_room(room_id, user_id)
        if not can_access:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have access to this room",
            )

        room = await room_service.get_room_with_members(room_id)
        if not room:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Room not found",
            )

        return [membership for membership in room.memberships if membership.is_active]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve room members: {str(e)}",
        )


@router.post(
    "/{room_id}/members",
    response_model=RoomMembershipRead,
    summary="Add member to room",
)
async def add_room_member(
    room_id: UUID = Path(..., description="Room ID to add member to"),
    request: RoomMembershipBase = None,  # Use existing RoomMembershipBase schema
    auth_client: AuthClientDep = None,
    room_service: RoomServiceDep = None,
):
    """
    Add a new member to a room.

    Only room owners and admins can add new members.
    Cannot add members if room is at capacity.
    """
    try:
        client, scoped_key = auth_client
        user_id = scoped_key.user_id if scoped_key else str(client.id)

        # Check user's role in room
        user_role = await room_service.get_member_role(room_id, user_id)
        if not user_role or user_role not in [MemberRole.owner, MemberRole.admin]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only room owners and admins can add members",
            )

        membership = await room_service.add_member(
            room_id=room_id,
            user_id=request.user_id,
            display_name=request.display_name,
            role=request.role,
        )

        if not membership:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User is already a member or room is at capacity",
            )

        return membership
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add member: {str(e)}",
        )


@router.delete(
    "/{room_id}/members/{user_id}",
    response_model=RoomResponse,
    summary="Remove member from room",
)
async def remove_room_member(
    room_id: UUID = Path(..., description="Room ID to remove member from"),
    user_id: str = Path(..., description="User ID to remove"),
    auth_client: AuthClientDep = None,
    room_service: RoomServiceDep = None,
):
    """
    Remove a member from a room.

    Room owners and admins can remove any member.
    Members can remove themselves.
    """
    try:
        client, scoped_key = auth_client
        current_user_id = scoped_key.user_id if scoped_key else str(client.id)

        # Check permissions
        if current_user_id != user_id:
            # Not removing self, check if user has admin privileges
            user_role = await room_service.get_member_role(room_id, current_user_id)
            if not user_role or user_role not in [MemberRole.owner, MemberRole.admin]:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You can only remove yourself or need admin privileges",
                )

        success = await room_service.remove_member(room_id, user_id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Member not found in room",
            )

        return RoomResponse(
            success=True,
            message="Member removed successfully",
            data={
                "room_id": str(room_id),
                "user_id": user_id,
            },
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to remove member: {str(e)}",
        )


# ==================== MEMBER ROLE MANAGEMENT ====================


@router.get("/{room_id}/members/{user_id}/role", summary="Get member role")
async def get_member_role(
    room_id: UUID = Path(..., description="Room ID"),
    user_id: str = Path(..., description="User ID to check role for"),
    auth_client: AuthClientDep = None,
    room_service: RoomServiceDep = None,
):
    """
    Get a member's role in a room.

    Only accessible to room members.
    """
    try:
        client, scoped_key = auth_client
        current_user_id = scoped_key.user_id if scoped_key else str(client.id)

        # Check if current user can access this room
        can_access = await room_service.user_can_access_room(room_id, current_user_id)
        if not can_access:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have access to this room",
            )

        role = await room_service.get_member_role(room_id, user_id)
        if not role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found in room",
            )

        return {
            "room_id": str(room_id),
            "user_id": user_id,
            "role": role.value,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get member role: {str(e)}",
        )
