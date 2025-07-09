# app/services/room.py
from uuid import UUID

import sqlalchemy
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.room import MemberRole, Room, RoomMembership
from app.schemas.room import RoomCreate, RoomUpdate
from app.services.base import BaseService


class RoomService(BaseService[Room, RoomCreate, RoomUpdate]):
    def __init__(self, db: AsyncSession):
        super().__init__(model=Room, db=db)

    async def create_room(
        self,
        client_id: UUID,
        creator_user_id: str,
        creator_display_name: str,
        room_data: RoomCreate,
    ) -> Room:
        """
        Create a new room and add creator as owner

        Args:
            client_id: The client ID
            creator_user_id: User ID of the room creator
            creator_display_name: Display name of the creator
            room_data: Room creation data

        Returns:
            Created room object
        """
        # Create room
        room = Room(
            client_id=client_id,
            name=room_data.name,
            description=room_data.description,
            room_type=room_data.room_type.value,
            max_members=room_data.max_members,
            created_by_user_id=creator_user_id,
        )

        self.db.add(room)
        await self.db.flush()  # Get the room ID

        # Add creator as owner
        membership = RoomMembership(
            room_id=room.id,
            user_id=creator_user_id,
            display_name=creator_display_name,
            role=MemberRole.owner.value,
        )

        self.db.add(membership)
        await self.db.commit()
        await self.db.refresh(room)

        return room

    async def get_user_rooms(self, user_id: str, client_id: UUID) -> list[Room]:
        """Get all rooms a user is a member of"""
        result = await self.db.execute(
            sqlalchemy.select(Room)
            .join(RoomMembership)
            .where(Room.client_id == client_id)
            .where(RoomMembership.user_id == user_id)
            .where(RoomMembership.is_active == True)  # noqa
            .where(Room.is_active == True)  # noqa
            .options(selectinload(Room.memberships))
        )
        return result.scalars().all()

    async def get_room_with_members(self, room_id: UUID) -> Room | None:
        """Get room with all its members"""
        result = await self.db.execute(
            sqlalchemy.select(Room)
            .where(Room.id == room_id)
            .options(selectinload(Room.memberships))
        )
        return result.scalar_one_or_none()

    async def add_member(
        self,
        room_id: UUID,
        user_id: str,
        display_name: str,
        role: MemberRole = MemberRole.member,
    ) -> RoomMembership | None:
        """Add a member to a room"""
        # Check if user is already a member
        existing = await self.db.execute(
            sqlalchemy.select(RoomMembership)
            .where(RoomMembership.room_id == room_id)
            .where(RoomMembership.user_id == user_id)
            .where(RoomMembership.is_active == True)  # noqa
        )

        if existing.scalar_one_or_none():
            return None  # User already a member

        # Check room member limit
        room = await self.get(id=room_id)
        if room and room.max_members:
            member_count = await self.db.execute(
                sqlalchemy.select(sqlalchemy.func.count(RoomMembership.id))
                .where(RoomMembership.room_id == room_id)
                .where(RoomMembership.is_active == True)  # noqa
            )
            if member_count.scalar() >= room.max_members:
                return None  # Room is full

        # Add member
        membership = RoomMembership(
            room_id=room_id,
            user_id=user_id,
            display_name=display_name,
            role=role.value,
        )

        self.db.add(membership)
        await self.db.commit()
        await self.db.refresh(membership)

        return membership

    async def remove_member(self, room_id: UUID, user_id: str) -> bool:
        """Remove a member from a room"""
        result = await self.db.execute(
            sqlalchemy.select(RoomMembership)
            .where(RoomMembership.room_id == room_id)
            .where(RoomMembership.user_id == user_id)
            .where(RoomMembership.is_active == True)  # noqa
        )

        membership = result.scalar_one_or_none()
        if membership:
            membership.is_active = False
            membership.left_at = sqlalchemy.func.now()
            await self.db.commit()
            return True
        return False

    async def user_can_access_room(self, room_id: UUID, user_id: str) -> bool:
        """Check if a user can access a room"""
        result = await self.db.execute(
            sqlalchemy.select(RoomMembership)
            .where(RoomMembership.room_id == room_id)
            .where(RoomMembership.user_id == user_id)
            .where(RoomMembership.is_active == True)  # noqa
        )
        return result.scalar_one_or_none() is not None

    async def get_member_role(self, room_id: UUID, user_id: str) -> MemberRole | None:
        """Get user's role in a room"""
        result = await self.db.execute(
            sqlalchemy.select(RoomMembership.role)
            .where(RoomMembership.room_id == room_id)
            .where(RoomMembership.user_id == user_id)
            .where(RoomMembership.is_active == True)  # noqa
        )
        role_str = result.scalar_one_or_none()
        return MemberRole(role_str) if role_str else None

    async def get_all_client_rooms(self, client_id: UUID) -> list[Room]:
        """Get all rooms for a client (admin view) with auto-deactivation check"""

        # First, check and deactivate rooms that have been inactive too long
        await self._check_and_deactivate_inactive_rooms(client_id)

        # Then return all active rooms
        result = await self.db.execute(
            sqlalchemy.select(Room)
            .where(Room.client_id == client_id)
            .where(Room.is_active == True)  # noqa
            .options(selectinload(Room.memberships))
            .order_by(Room.last_message_at.desc().nullslast(), Room.created_at.desc())
        )
        return result.scalars().all()

    async def _check_and_deactivate_inactive_rooms(self, client_id: UUID) -> int:
        """Check and deactivate rooms that have been inactive for too long"""
        from datetime import datetime, timedelta

        from app.models.room import ROOM_INACTIVITY_SETTINGS

        deactivated_count = 0
        current_time = datetime.now()

        # Get all active rooms for the client
        result = await self.db.execute(
            sqlalchemy.select(Room)
            .where(Room.client_id == client_id)
            .where(Room.is_active == True)  # noqa
        )
        rooms = result.scalars().all()

        for room in rooms:
            # Get inactivity threshold for this room type
            inactivity_days = ROOM_INACTIVITY_SETTINGS.get(room.room_type, 30)
            cutoff_date = current_time - timedelta(days=inactivity_days)

            # Check if room should be deactivated
            should_deactivate = False

            if room.last_message_at is None:
                # No messages ever sent - check creation date
                if room.created_at < cutoff_date:
                    should_deactivate = True
            else:
                # Check last message date
                if room.last_message_at < cutoff_date:
                    should_deactivate = True

            if should_deactivate:
                room.is_active = False
                room.deactivated_reason = "auto_inactive"
                room.deactivated_at = current_time
                deactivated_count += 1

        if deactivated_count > 0:
            await self.db.commit()

        return deactivated_count


def get_room_service(db: AsyncSession) -> RoomService:
    return RoomService(db)
