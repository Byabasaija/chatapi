from fastapi import APIRouter

from app.api.api_v1.routes import client, utils

# Create the main API router
rest_api_router = APIRouter()

# Include sub-routers with consistent prefixes and tags
rest_api_router.include_router(utils.router, prefix="/utils", tags=["utils"])

rest_api_router.include_router(client.router, prefix="/client", tags=["client"])
