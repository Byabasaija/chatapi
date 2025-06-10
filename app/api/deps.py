# deps.py
from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import async_session_maker
from app.models.client import Client
from app.services.client import ClientService, get_client_service
from app.services.message import MessageService, get_message_service


async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


AsyncSessionDep = Annotated[AsyncSession, Depends(get_async_db)]


def get_client_service_dep(db: AsyncSessionDep) -> ClientService:
    return get_client_service(db)


ClientServiceDep = Annotated[ClientService, Depends(get_client_service_dep)]


# Auth dependency that validates API key
async def validate_api_key(api_key: str, client_service: ClientServiceDep) -> Client:
    client = await client_service.verify_api_key(api_key)
    if not client:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    return client


# Use this as a dependency for protected endpoints
AuthClientDep = Annotated[Client, Depends(validate_api_key)]


def get_message_service_dep(db: AsyncSessionDep) -> MessageService:
    return get_message_service(db)


MessageServiceDep = Annotated[MessageService, Depends(get_message_service_dep)]
