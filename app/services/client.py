# app/services/client.py
import secrets
from uuid import UUID

import sqlalchemy
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_api_key
from app.models.client import Client, EncryptionMode
from app.schemas.client import ClientCreate, ClientUpdate
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
            Tuple containing the saved client object and the raw unhashed API key
        """
        # Generate secure API key
        raw_key = secrets.token_urlsafe(32)
        hashed_key = hash_api_key(raw_key)

        # Create client object
        client = Client(
            name=payload.name,
            api_key=hashed_key,
            encryption_mode=payload.encryption_mode.value,
        )

        # Save to database
        self.db.add(client)
        await self.db.commit()
        await self.db.refresh(client)

        return client, raw_key

    async def get_by_api_key(self, api_key: str) -> Client | None:
        """Get a client by API key"""
        hashed_key = hash_api_key(api_key)
        result = await self.db.execute(
            sqlalchemy.select(Client).where(Client.api_key == hashed_key)
        )
        return result.scalars().first()

    async def verify_api_key(self, api_key: str) -> Client | None:
        """Verify an API key and return the client if valid"""
        client = await self.get_by_api_key(api_key)
        if client:
            return client
        return None

    async def update_encryption_mode(
        self, *, client_id: UUID, encryption_mode: EncryptionMode
    ) -> Client | None:
        """Update a client's encryption mode"""
        client = await self.get(id=client_id)
        if client:
            return await self.update(
                db_obj=client, obj_in={"encryption_mode": encryption_mode.value}
            )
        return None

    # Factory function that can be used in FastAPI dependencies


def get_client_service(db: AsyncSession) -> ClientService:
    return ClientService(db)
