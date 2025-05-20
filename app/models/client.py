from datetime import datetime
from enum import Enum
from uuid import uuid4

from sqlalchemy import Column, DateTime, String, text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import validates

from app.db.base_class import Base


class EncryptionMode(str, Enum):
    E2EE = "e2ee"
    NONE = "none"


class Client(Base):
    __tablename__ = "clients"

    id = Column(
        PGUUID,
        primary_key=True,
        default=uuid4,
        server_default=text("gen_random_uuid()"),
    )
    name = Column(String, nullable=True)
    encryption_mode = Column(String, default=EncryptionMode.NONE.value, nullable=False)
    api_key = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    @validates("encryption_mode")
    def validate_encryption_mode(self, key, value):
        # Ensure the value is a valid EncryptionMode
        if isinstance(value, str) and value not in [e.value for e in EncryptionMode]:
            raise ValueError(f"Invalid encryption mode: {value}")
        return value
