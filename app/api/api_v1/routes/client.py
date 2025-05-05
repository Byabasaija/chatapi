import secrets

from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.api.deps import get_db
from app.core.security import hash_api_key
from app.db.models.api_client import APIClient, APIClientCreate, APIClientReadWithKey

router = APIRouter()


@router.post("/register", response_model=APIClientReadWithKey)
def register_client(payload: APIClientCreate, session: Session = Depends(get_db)):
    # Generate a random secure API key
    raw_key = secrets.token_urlsafe(32)  # Return this only once

    # Hash the key
    hashed_key = hash_api_key(raw_key)

    client = APIClient(name=payload.name, api_key=hashed_key)
    session.add(client)
    session.commit()
    session.refresh(client)

    return {
        "id": client.id,
        "created_at": client.created_at,
        "name": client.name,
        # send raw key here as part of response once
        "api_key": raw_key,
    }
