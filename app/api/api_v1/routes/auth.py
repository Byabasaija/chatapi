# app/api/api_v1/routes/auth.py

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from app.api.deps import AuthClientDep, ClientServiceDep
from app.models.client import ScopedKeyPermission
from app.schemas.client import (
    UserLoginRequest,
    UserLoginResponse,
)

router = APIRouter()


class ErrorResponse(BaseModel):
    detail: str
    error_code: str | None = None


@router.post(
    "/login", response_model=UserLoginResponse, summary="User Login/Authentication"
)
async def user_login(
    user_data: UserLoginRequest,
    current_client: AuthClientDep,
    client_service: ClientServiceDep,
):
    """
    Authenticate a user and always rotate their scoped API key.

    **Security Enhancement**: This endpoint ALWAYS creates a new API key and revokes
    any existing key for the user. This ensures:
    - Fresh credentials on every login
    - Automatic cleanup of potentially compromised keys
    - Simplified frontend logic (always use the returned key)

    **Requirements:**
    - Must be called with a master API key in the Authorization header
    - The user_id should be unique within your client's scope
    - This endpoint should be called server side to avoid exposing the master key to browsers
    - Be sure to provider the users permissions

    **Response:**
    - Always returns a new `api_key` that should be stored by the frontend
    - Any previous API key for this user is automatically revoked

    **Note:** This endpoint is designed for user authentication and should not be used
    for client registration or management. Use the `/clients` endpoints for that.
    """
    try:
        client, scoped_key = current_client

        # Only master API keys can authenticate users
        if scoped_key:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only master API key can authenticate users",
            )

        # Convert string permissions to enum
        permissions = [ScopedKeyPermission(perm) for perm in user_data.permissions]

        # Always reset/rotate the user's key for enhanced security
        new_key, raw_key = await client_service.reset_user_key(
            client_id=client.id,
            user_id=user_data.user_id,
            permissions=permissions,
        )

        return UserLoginResponse(
            user_id=new_key.user_id,
            display_name=user_data.display_name or user_data.user_id,
            api_key=raw_key,
            permissions=[ScopedKeyPermission(perm) for perm in new_key.permissions],
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to authenticate user: {str(e)}",
        )


@router.post("/logout", summary="User Logout")
async def user_logout(
    user_id: str,
    current_client: AuthClientDep,
    client_service: ClientServiceDep,
):
    """
    Logout a user by revoking their scoped API key.

    **Note:** This permanently revokes the user's API key. They will need to
    re-authenticate to get a new key.

    **Requirements:**
    - Must be called with a master API key
    """
    try:
        client, scoped_key = current_client

        # Only master API keys can logout users
        if scoped_key:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only master API key can logout users",
            )

        # Find the user's scoped key
        existing_key = await client_service.get_scoped_key_for_user(client.id, user_id)

        if not existing_key:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found or not authenticated",
            )

        # Revoke the scoped key
        success = await client_service.revoke_scoped_key(existing_key.id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to logout user",
            )

        return {
            "message": f"User {user_id} successfully logged out",
            "user_id": user_id,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to logout user: {str(e)}",
        )
