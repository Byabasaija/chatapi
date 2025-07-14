# app/api/api_v1/routes/client.py
# ruff : noqa
from typing import Any
from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from app.api.deps import AuthClientDep, ClientServiceDep
from app.models.client import ScopedKeyPermission
from app.providers import EmailProviderManager
from app.schemas.client import (
    APIClientReadWithKey,
    ClientCreate,
    ClientRead,
    ClientUpdate,
    ScopedKeyCreate,
    ScopedKeyRead,
    ScopedKeyReadWithKey,
)
from app.schemas.email_config import EmailProviderConfig

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


@router.put("/me")
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

    return {
        "message": "Client information updated successfully",
        "client_id": str(updated_client.id),
        "updated_fields": list(client_update.model_dump(exclude_unset=True).keys()),
    }


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

    scoped_key, raw_key, created = await client_service.get_or_create_user_scoped_key(
        client_id=client.id, user_id=scoped_key_data.user_id, permissions=permissions
    )

    result = ScopedKeyReadWithKey.model_validate(scoped_key)
    result.scoped_api_key = raw_key
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


@router.put("/me/email-providers")
async def update_email_providers(
    provider_configs: list[EmailProviderConfig],
    current_client: AuthClientDep,
    client_service: ClientServiceDep,
):
    """Create or Update email provider configurations for current client."""
    client, scoped_key = current_client

    if scoped_key:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only master API key can update email providers",
        )

    # Validate all provider configurations
    manager = EmailProviderManager([config.model_dump() for config in provider_configs])
    await manager.initialize_providers()

    validation_results = await manager.validate_all_providers()
    invalid_providers = [
        name
        for name, result in validation_results.items()
        if not result.get("valid", False)
    ]

    if invalid_providers:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid provider configurations: {', '.join(invalid_providers)}",
        )

    # Save to database
    updated_client = await client_service.update_email_providers(
        client_id=client.id,
        provider_configs=[config.model_dump() for config in provider_configs],
    )

    return {
        "message": "Email providers updated successfully",
        "provider_count": len(provider_configs),
    }


@router.get("/me/email-providers")
async def get_email_providers(
    current_client: AuthClientDep,
    client_service: ClientServiceDep,
) -> dict[str, Any]:
    """Get email provider configurations for current client."""
    client, scoped_key = current_client

    if scoped_key:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only master API key can view email providers",
        )

    provider_configs = await client_service.get_email_providers(client.id)

    # Return configs without sensitive data (API keys, passwords)
    sanitized_configs = []
    for config in provider_configs:
        sanitized_config = {
            "provider_type": config.get("provider_type"),
            "is_primary": config.get("is_primary", False),
            "is_bulk": config.get("is_bulk", True),
            "max_recipients": config.get("max_recipients", 100),
            "rate_limit_per_second": config.get("rate_limit_per_second", 10),
        }
        # Include non-sensitive config fields
        provider_config = config.get("config", {})
        if "from_email" in provider_config:
            sanitized_config["from_email"] = provider_config["from_email"]
        if "from_name" in provider_config:
            sanitized_config["from_name"] = provider_config["from_name"]
        if "host" in provider_config:  # For SMTP
            sanitized_config["host"] = provider_config["host"]
        if "port" in provider_config:  # For SMTP
            sanitized_config["port"] = provider_config["port"]

        sanitized_configs.append(sanitized_config)

    return {
        "provider_configs": sanitized_configs,
        "total_count": len(provider_configs),
    }


@router.post("/me/email-providers/validate")
async def validate_email_providers(
    provider_configs: list[EmailProviderConfig],
    current_client: AuthClientDep,
):
    """Validate email provider configurations for current client without saving them."""
    client, scoped_key = current_client

    if scoped_key:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only master API key can validate email providers",
        )

    # Validate all provider configurations
    manager = EmailProviderManager([config.model_dump() for config in provider_configs])
    await manager.initialize_providers()

    validation_results = await manager.validate_all_providers()

    return {
        "validation_results": validation_results,
        "all_valid": all(
            result.get("valid", False) for result in validation_results.values()
        ),
    }
