from datetime import datetime
from uuid import UUID, uuid4

from sqlmodel import Field, SQLModel


class APIClientBase(SQLModel):
    name: str | None = None


class APIClient(APIClientBase, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    api_key: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class APIClientRead(APIClientBase):
    id: UUID
    created_at: datetime


class APIClientCreate(APIClientBase):
    pass  # no api_key, server handles it


class APIClientReadWithKey(APIClientRead):
    api_key: str
