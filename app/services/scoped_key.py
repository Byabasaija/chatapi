# app/services/scoped_key.py
from uuid import UUID

import sqlalchemy
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.security import verify_api_key
from app.models.client import ScopedKey, ScopedKeyPermission
from app.schemas.client import ScopedKeyCreate, ScopedKeyUpdate
from app.services.base import BaseService


class ScopedKeyService(BaseService[ScopedKey, ScopedKeyCreate, ScopedKeyUpdate]):
    def __init__(self, db: AsyncSession):
        super().__init__(model=ScopedKey, db=db)

    async def get_by_scoped_api_key(self, api_key: str) -> ScopedKey | None:
        """Get a scoped key by API key using optimized database query"""
        # Get all active scoped keys
        result = await self.db.execute(
            sqlalchemy.select(ScopedKey)
            .where(ScopedKey.is_active is True)
            .options(selectinload(ScopedKey.client))
        )
        scoped_keys = result.scalars().all()

        # Verify against each hashed key
        for scoped_key in scoped_keys:
            if verify_api_key(api_key, scoped_key.scoped_api_key):
                # Update last used timestamp
                scoped_key.last_used_at = sqlalchemy.func.now()
                await self.db.commit()
                return scoped_key

        return None

    async def verify_scoped_api_key(self, api_key: str) -> ScopedKey | None:
        """Verify a scoped API key and return the scoped key if valid"""
        return await self.get_by_scoped_api_key(api_key)

    async def has_permission(
        self, scoped_key: ScopedKey, permission: ScopedKeyPermission
    ) -> bool:
        """Check if a scoped key has a specific permission"""
        return permission.value in scoped_key.permissions

    async def get_user_scoped_keys(
        self, client_id: UUID, user_id: str
    ) -> list[ScopedKey]:
        """Get all scoped keys for a specific user within a client"""
        result = await self.db.execute(
            sqlalchemy.select(ScopedKey)
            .where(ScopedKey.client_id == client_id)
            .where(ScopedKey.user_id == user_id)
            .where(ScopedKey.is_active is True)
        )
        return result.scalars().all()

    async def update_permissions(
        self, scoped_key_id: UUID, permissions: list[ScopedKeyPermission]
    ) -> ScopedKey | None:
        """Update permissions for a scoped key"""
        scoped_key = await self.get(id=scoped_key_id)
        if scoped_key:
            scoped_key.permissions = [perm.value for perm in permissions]
            await self.db.commit()
            await self.db.refresh(scoped_key)
            return scoped_key
        return None


def get_scoped_key_service(db: AsyncSession) -> ScopedKeyService:
    return ScopedKeyService(db)
