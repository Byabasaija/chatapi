from fastapi import APIRouter

from app.api.api_v1.routes import client, utils

# Create the main API router
api_router = APIRouter()

# Include sub-routers with consistent prefixes and tags
api_router.include_router(utils.router, prefix="/utils", tags=["utils"])

api_router.include_router(client.router, prefix="/client", tags=["client"])
