# app/services/client.py
import secrets
from uuid import UUID

import sqlalchemy
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import (
    decrypt_provider_configs,
    encrypt_provider_configs,
    hash_api_key,
    verify_api_key,
)
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
            sqlalchemy.select(Client).where(Client.is_active == True)  # noqa
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
            .where(ScopedKey.is_active == True)  # noqa
        )
        return result.scalars().all()

    async def verify_scoped_api_key(
        self, api_key: str
    ) -> tuple[Client, ScopedKey] | None:  # noqa
        """Verify a scoped API key and return the client and scoped key if valid"""
        # Get all active scoped keys with their clients
        result = await self.db.execute(
            sqlalchemy.select(ScopedKey, Client)
            .join(Client)
            .where(ScopedKey.is_active == True)  # noqa
            .where(Client.is_active == True)  # noqa
        )

        for scoped_key, client in result.all():
            if verify_api_key(api_key, scoped_key.scoped_api_key):
                return client, scoped_key

        return None

    async def get_scoped_key_for_user(
        self, client_id: UUID, user_id: str
    ) -> ScopedKey | None:
        """Get an existing active scoped key for a user within a client"""
        result = await self.db.execute(
            sqlalchemy.select(ScopedKey)
            .where(ScopedKey.client_id == client_id)
            .where(ScopedKey.user_id == user_id)
            .where(ScopedKey.is_active == True)  # noqa
        )
        return result.scalar_one_or_none()

    async def get_or_create_user_scoped_key(
        self, client_id: UUID, user_id: str, permissions: list[ScopedKeyPermission]
    ) -> tuple[ScopedKey, str, bool]:
        """
        Get existing scoped key for user or create a new one

        Args:
            client_id: The client ID
            user_id: User ID from the integrating client
            permissions: List of permissions for this scoped key

        Returns:
            Tuple containing (scoped_key, raw_api_key, is_new_key)
        """
        # Check if scoped key already exists for this user
        existing_key = await self.get_scoped_key_for_user(client_id, user_id)

        if existing_key:
            # Return the existing key but we can't return the raw key since it's hashed
            # For existing keys, we return None as raw key and indicate it's not new
            return existing_key, existing_key.scoped_api_key, False

        # Create new scoped key
        scoped_key, raw_key = await self.create_scoped_key(
            client_id, user_id, permissions
        )
        return scoped_key, raw_key, True

    async def revoke_scoped_key(self, scoped_key_id: UUID) -> bool:
        """Revoke a scoped key"""
        scoped_key = await self.db.get(ScopedKey, scoped_key_id)
        if scoped_key:
            scoped_key.is_active = False
            await self.db.commit()
            return True
        return False

    async def delete_scoped_key(self, scoped_key_id: UUID) -> bool:
        """Permanently delete a scoped key"""
        scoped_key = await self.db.get(ScopedKey, scoped_key_id)
        if scoped_key:
            await self.db.delete(scoped_key)
            await self.db.commit()
            return True
        return False

    async def reset_user_key(
        self,
        client_id: UUID,
        user_id: str,
        permissions: list[ScopedKeyPermission] | None = None,
    ) -> tuple[ScopedKey, str]:
        """
        Reset a user's API key by deleting the old one and creating a new one.

        Args:
            client_id: The client ID
            user_id: The user identifier
            permissions: Optional new permissions. If None, uses existing permissions

        Returns:
            Tuple containing (new_scoped_key, raw_api_key)
        """
        # Get the existing key to preserve permissions if not specified
        existing_key = await self.get_scoped_key_for_user(client_id, user_id)

        if existing_key:
            # Use existing permissions if not provided
            if permissions is None:
                permissions = [
                    ScopedKeyPermission(perm) for perm in existing_key.permissions
                ]

            # Delete the old key entirely to avoid unique constraint violation
            # We need to delete and flush to ensure the constraint is released
            await self.db.delete(existing_key)
            await self.db.flush()  # Ensure delete is processed before insert
        else:
            # If no existing key, use default permissions
            if permissions is None:
                permissions = [
                    ScopedKeyPermission.READ_MESSAGES,
                    ScopedKeyPermission.SEND_MESSAGES,
                ]

        # Generate secure scoped API key
        raw_key = secrets.token_urlsafe(32)
        hashed_key = hash_api_key(raw_key)

        # Create new scoped key object
        new_scoped_key = ScopedKey(
            client_id=client_id,
            user_id=user_id,
            scoped_api_key=hashed_key,
            permissions=[perm.value for perm in permissions],
        )

        # Add to database and commit both operations in same transaction
        self.db.add(new_scoped_key)
        await self.db.commit()
        await self.db.refresh(new_scoped_key)

        return new_scoped_key, raw_key

    async def update_email_providers(
        self, client_id: UUID, provider_configs: list[dict]
    ) -> Client:
        """Update email provider configurations for a client with encryption at rest."""
        client = await self.get(client_id)
        if not client:
            raise ValueError(f"Client {client_id} not found")

        # Encrypt sensitive fields before storing
        encrypted_configs = encrypt_provider_configs(provider_configs)
        client.email_provider_configs = encrypted_configs
        await self.db.commit()
        await self.db.refresh(client)
        return client

    async def get_email_providers(self, client_id: UUID) -> list[dict]:
        """Get email provider configurations for a client with decryption."""
        client = await self.get(client_id)
        if not client:
            raise ValueError(f"Client {client_id} not found")

        encrypted_configs = client.email_provider_configs or []
        # Decrypt sensitive fields before returning
        return decrypt_provider_configs(encrypted_configs)


def get_client_service(db: AsyncSession) -> ClientService:
    return ClientService(db)
