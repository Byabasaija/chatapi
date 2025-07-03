# app/services/client.py
import secrets
from uuid import UUID

import sqlalchemy
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_api_key, verify_api_key
from app.models.client import Client, ScopedKey, ScopedKeyPermission
from app.schemas.client import (
    ClientCreate,
    ClientUpdate,
)
from app.services.base import BaseService


class ClientService(BaseService[Client, ClientCreate, ClientUpdate]):
    def __init__(self, db: AsyncSession):
        super().__init__(model=Client, db=db)

    async def register_new_client(self, payload: ClientCreate) -> tuple[Client, str]:
        """
        Register a new API client in the system

        Args:
            payload: Client creation data

        Returns:
            Tuple containing the saved client object and the raw unhashed master API key
        """
        # Generate secure master API key
        raw_key = secrets.token_urlsafe(32)
        hashed_key = hash_api_key(raw_key)

        # Create client object
        client = Client(
            name=payload.name,
            master_api_key=hashed_key,
        )

        # Save to database
        self.db.add(client)
        await self.db.commit()
        await self.db.refresh(client)

        return client, raw_key

    async def get_by_master_api_key(self, api_key: str) -> Client | None:
        """Get a client by master API key using optimized database query"""
        # Get all clients with their hashed keys
        result = await self.db.execute(
            sqlalchemy.select(Client).where(Client.is_active is True)
        )
        clients = result.scalars().all()

        # Verify against each hashed key
        for client in clients:
            if verify_api_key(api_key, client.master_api_key):
                return client

        return None

    async def verify_master_api_key(self, api_key: str) -> Client | None:
        """Verify a master API key and return the client if valid"""
        return await self.get_by_master_api_key(api_key)

    async def create_scoped_key(
        self, client_id: UUID, user_id: str, permissions: list[ScopedKeyPermission]
    ) -> tuple[ScopedKey, str]:
        """
        Create a scoped API key for a user within a client

        Args:
            client_id: The client ID
            user_id: User ID from the integrating client
            permissions: List of permissions for this scoped key

        Returns:
            Tuple containing the scoped key object and raw API key
        """
        # Generate secure scoped API key
        raw_key = secrets.token_urlsafe(32)
        hashed_key = hash_api_key(raw_key)

        # Create scoped key object
        scoped_key = ScopedKey(
            client_id=client_id,
            user_id=user_id,
            scoped_api_key=hashed_key,
            permissions=[perm.value for perm in permissions],
        )

        # Save to database
        self.db.add(scoped_key)
        await self.db.commit()
        await self.db.refresh(scoped_key)

        return scoped_key, raw_key

    async def get_scoped_keys_for_client(self, client_id: UUID) -> list[ScopedKey]:
        """Get all scoped keys for a client"""
        result = await self.db.execute(
            sqlalchemy.select(ScopedKey)
            .where(ScopedKey.client_id == client_id)
            .where(ScopedKey.is_active is True)
        )
        return result.scalars().all()

    async def revoke_scoped_key(self, scoped_key_id: UUID) -> bool:
        """Revoke a scoped key"""
        scoped_key = await self.db.get(ScopedKey, scoped_key_id)
        if scoped_key:
            scoped_key.is_active = False
            await self.db.commit()
            return True
        return False


def get_client_service(db: AsyncSession) -> ClientService:
    return ClientService(db)
