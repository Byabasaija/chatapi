# app/api/api_v1/routes/client.py
from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from app.api.deps import AuthClientDep, ClientServiceDep
from app.models.client import ScopedKeyPermission
from app.schemas.client import (
    APIClientReadWithKey,
    ClientCreate,
    ClientRead,
    ClientUpdate,
    ScopedKeyCreate,
    ScopedKeyRead,
    ScopedKeyReadWithKey,
)

router = APIRouter()


@router.post("/", response_model=APIClientReadWithKey)
async def create_api_client(
    client_data: ClientCreate,
    client_service: ClientServiceDep,
):
    """
    Create a new API client and return the client details along with the master API key.
    This is a public endpoint for initial client registration.
    """
    client, raw_key = await client_service.register_new_client(client_data)

    # Convert DB model to Pydantic model with raw key included
    result = APIClientReadWithKey.model_validate(client)
    result.master_api_key = raw_key  # Use the raw key in the response

    return result


@router.get("/me")
async def get_current_details(
    current_client: AuthClientDep,
):
    """
    Get current client or scoped key information based on the API key provided.
    Returns client details for master keys, scoped key details for scoped keys.
    """
    client, scoped_key = current_client

    if scoped_key:
        # Scoped key was used - return scoped key details
        return {
            "type": "scoped_key",
            "client_id": str(client.id),
            "client_name": client.name,
            "scoped_key": {
                "id": str(scoped_key.id),
                "user_id": scoped_key.user_id,
                "permissions": scoped_key.permissions,
                "is_active": scoped_key.is_active,
                "created_at": scoped_key.created_at,
                "updated_at": scoped_key.updated_at,
            },
        }
    else:
        # Master key was used - return client details
        return {
            "type": "client",
            "client": {
                "id": str(client.id),
                "name": client.name,
                "is_active": client.is_active,
                "created_at": client.created_at,
                "updated_at": client.updated_at,
            },
        }


@router.put("/me", response_model=ClientRead)
async def update_current_client(
    client_update: ClientUpdate,
    current_client: AuthClientDep,
    client_service: ClientServiceDep,
):
    """
    Update current client information. Only accessible with master API key.
    """
    client, scoped_key = current_client

    if scoped_key:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only master API key can update client information",
        )

    updated_client = await client_service.update(db_obj=client, obj_in=client_update)
    return updated_client


@router.post("/scoped-keys", response_model=ScopedKeyReadWithKey)
async def create_scoped_key(
    scoped_key_data: ScopedKeyCreate,
    current_client: AuthClientDep,
    client_service: ClientServiceDep,
):
    """
    Create a new scoped API key. Only accessible with master API key.
    """
    client, scoped_key = current_client

    if scoped_key:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only master API key can create scoped keys",
        )

    # Convert string permissions to enum
    permissions = [ScopedKeyPermission(perm) for perm in scoped_key_data.permissions]

    scoped_key_obj, raw_key = await client_service.create_scoped_key(
        client_id=client.id, user_id=scoped_key_data.user_id, permissions=permissions
    )

    # Convert to response model and include raw key
    result = ScopedKeyReadWithKey.model_validate(scoped_key_obj)
    result.api_key = raw_key

    return result


@router.get("/scoped-keys", response_model=list[ScopedKeyRead])
async def list_scoped_keys(
    current_client: AuthClientDep,
    client_service: ClientServiceDep,
):
    """
    List all scoped keys for the current client. Only accessible with master API key.
    """
    client, scoped_key = current_client

    if scoped_key:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only master API key can list scoped keys",
        )

    scoped_keys = await client_service.get_scoped_keys_for_client(client.id)
    return scoped_keys


@router.delete("/scoped-keys/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_scoped_key(
    key_id: UUID,
    current_client: AuthClientDep,
    client_service: ClientServiceDep,
):
    """
    Revoke a scoped API key. Only accessible with master API key.
    """
    client, scoped_key = current_client

    if scoped_key:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only master API key can revoke scoped keys",
        )

    success = await client_service.revoke_scoped_key(key_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Scoped key not found"
        )

    return None
