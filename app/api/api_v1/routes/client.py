# app/api/routes/clients.py
from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from app.api.deps import AuthClientDep, ClientServiceDep
from app.schemas.client import (
    APIClientReadWithKey,
    ClientCreate,
    ClientRead,
    ClientUpdate,
)

router = APIRouter()


@router.post("/", response_model=APIClientReadWithKey)
async def create_api_client(
    client_data: ClientCreate,
    client_service: ClientServiceDep,
):
    """
    Create a new API client and return the client details along with the API key
    """
    client, raw_key = await client_service.register_new_client(client_data)

    # Convert DB model to Pydantic model with raw key included
    result = APIClientReadWithKey.model_validate(client)
    result.api_key = raw_key  # Use the raw key in the response

    return result


@router.get("/me", response_model=ClientRead)
async def get_current_client(
    current_client: AuthClientDep,
):
    """
    Get current client information based on API key
    """
    return current_client


@router.get("/{client_id}", response_model=ClientRead)
async def get_client(
    client_id: UUID,
    client_service: ClientServiceDep,
):
    """
    Get a specific client by ID
    """
    client = await client_service.get(id=client_id)
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Client not found"
        )
    return client


@router.put("/{client_id}", response_model=ClientRead)
async def update_client(
    client_id: UUID,
    client_update: ClientUpdate,
    client_service: ClientServiceDep,
):
    """
    Update a client
    """
    client = await client_service.get(id=client_id)
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Client not found"
        )
    updated_client = await client_service.update(db_obj=client, obj_in=client_update)
    return updated_client
