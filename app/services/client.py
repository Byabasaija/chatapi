import secrets

from sqlmodel import Session

from app.core.security import hash_api_key
from app.models.api_client import APIClient, APIClientCreate


def register_new_client(
    payload: APIClientCreate, session: Session
) -> tuple[APIClient, str]:
    raw_key = secrets.token_urlsafe(32)
    hashed_key = hash_api_key(raw_key)

    client = APIClient(name=payload.name, api_key=hashed_key)
    session.add(client)
    session.commit()
    session.refresh(client)

    return client, raw_key
