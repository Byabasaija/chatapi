from fastapi import APIRouter

from app.api.routes import  utils
from app.core.config import settings

api_router = APIRouter()
api_router.include_router(utils.router)

