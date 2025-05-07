from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.api.deps import get_db
from app.models.api_client import APIClientCreate, APIClientReadWithKey
from app.services.client import register_new_client

router = APIRouter()


@router.post("/register", response_model=APIClientReadWithKey)
def register_client(payload: APIClientCreate, session: Session = Depends(get_db)):
    client, raw_key = register_new_client(payload, session)
    return {
        "id": client.id,
        "created_at": client.created_at,
        "name": client.name,
        "api_key": raw_key,
    }
