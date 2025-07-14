from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import async_session_maker
from app.models.client import Client, ScopedKey
from app.services.client import ClientService, get_client_service
from app.services.message import MessageService, get_message_service
from app.services.notification import NotificationService, get_notification_service
from app.services.room import RoomService, get_room_service

security = HTTPBearer()


@asynccontextmanager
async def get_db_session_context():
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    async with get_db_session_context() as session:
        yield session


AsyncSessionDep = Annotated[AsyncSession, Depends(get_async_db)]


def get_client_service_dep(db: AsyncSessionDep) -> ClientService:
    return get_client_service(db)


ClientServiceDep = Annotated[ClientService, Depends(get_client_service_dep)]


# Extract API key from Authorization Bearer header
async def get_api_key_from_header(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> str:
    """
    Extracts and returns the api key from the request headers.

    Args:
        credentials (HTTPAuthorizationCredentials): The credentials provided by the HTTPBearer security scheme.

    Returns:
        str: The extracted key.

    Raises:
        HTTPException: If the key is missing or invalid.
    """
    key = credentials.credentials

    if not key:
        raise HTTPException(
            status_code=403, detail="API key missing from authorization header"
        )
    return key


# Validate ANY API key (master or scoped) - for flexible endpoints
async def validate_any_api_key(
    api_key: Annotated[str, Depends(get_api_key_from_header)],
    client_service: ClientServiceDep,
) -> tuple[Client, ScopedKey | None]:
    """
    Validate any API key (master or scoped) and return client + optional scoped key
    Returns (client, None) for master keys, (client, scoped_key) for scoped keys
    """
    # Try master key first
    client = await client_service.verify_master_api_key(api_key)
    if client:
        return client, None

    # Try scoped key
    result = await client_service.verify_scoped_api_key(api_key)
    if result:
        return result

    # Neither worked
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid API key",
        headers={"WWW-Authenticate": "ApiKey"},
    )


AuthClientDep = Annotated[
    tuple[Client, ScopedKey | None], Depends(validate_any_api_key)
]


def get_message_service_dep(db: AsyncSessionDep) -> MessageService:
    return get_message_service(db)


MessageServiceDep = Annotated[MessageService, Depends(get_message_service_dep)]


def get_room_service_dep(db: AsyncSessionDep) -> RoomService:
    return get_room_service(db)


RoomServiceDep = Annotated[RoomService, Depends(get_room_service_dep)]


def get_notification_service_dep(db: AsyncSessionDep) -> NotificationService:
    return get_notification_service(db)


NotificationServiceDep = Annotated[
    NotificationService, Depends(get_notification_service_dep)
]
