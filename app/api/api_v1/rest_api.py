from fastapi import APIRouter

from app.api.api_v1.routes import client, message, room, utils

# Create the main API router
rest_api_router = APIRouter()

# Include sub-routers with consistent prefixes and tags
rest_api_router.include_router(utils.router, prefix="/utils", tags=["utils"])
rest_api_router.include_router(client.router, prefix="/clients", tags=["clients"])
rest_api_router.include_router(message.router, prefix="/messages", tags=["messages"])
rest_api_router.include_router(room.router, prefix="/rooms", tags=["rooms"])
