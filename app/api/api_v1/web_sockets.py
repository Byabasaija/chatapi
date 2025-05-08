from fastapi import APIRouter

from app.api.api_v1.routes import messages

# Create the main API router
web_sockets_router = APIRouter()

web_sockets_router.include_router(messages.router, prefix="/ws", tags=["websocket"])
