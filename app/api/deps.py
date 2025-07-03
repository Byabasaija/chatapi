# deps.py
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import async_session_maker
from app.models.client import Client, ScopedKey
from app.services.client import ClientService, get_client_service
from app.services.message import MessageService, get_message_service


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


# Extract API key from Authorization header
async def get_api_key_from_header(
    authorization: Annotated[str | None, Header()] = None,
    x_api_key: Annotated[str | None, Header(alias="X-API-Key")] = None,
) -> str:
    """
    Extract API key from either Authorization header (Bearer token) or X-API-Key header
    """
    api_key = None

    # Try Authorization header first (Bearer token)
    if authorization:
        if authorization.startswith("Bearer "):
            api_key = authorization[7:]  # Remove "Bearer " prefix
        else:
            # Direct API key in Authorization header
            api_key = authorization

    # Fall back to X-API-Key header
    elif x_api_key:
        api_key = x_api_key

    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required. Provide it in Authorization header (Bearer token) or X-API-Key header",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    return api_key


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
