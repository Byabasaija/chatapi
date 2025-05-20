from fastapi import APIRouter

from app.api.api_v1.routes import websocket

# Create the main API router
web_sockets_router = APIRouter()

web_sockets_router.include_router(websocket.router)
