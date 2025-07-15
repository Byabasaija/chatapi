import base64
import json
from typing import Any

from cryptography.fernet import Fernet
from passlib.context import CryptContext

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# Create encryption key from SECRET_KEY
def _get_encryption_key() -> bytes:
    """Generate a consistent encryption key from the SECRET_KEY."""
    # Use the first 32 bytes of SECRET_KEY, base64 encoded for Fernet
    key_bytes = settings.SECRET_KEY.encode()[:32]
    # Pad to 32 bytes if needed
    key_bytes = key_bytes.ljust(32, b"0")
    return base64.urlsafe_b64encode(key_bytes)


_fernet = Fernet(_get_encryption_key())


def hash_api_key(key: str) -> str:
    return pwd_context.hash(key)


def verify_api_key(plain_key: str, hashed_key: str) -> bool:
    return pwd_context.verify(plain_key, hashed_key)


def encrypt_provider_config(config: dict[str, Any]) -> str:
    """
    Encrypt email provider configuration containing sensitive data.

    Args:
        config: Provider configuration dictionary

    Returns:
        Base64 encoded encrypted string
    """
    config_json = json.dumps(config, sort_keys=True)
    encrypted_bytes = _fernet.encrypt(config_json.encode())
    return base64.urlsafe_b64encode(encrypted_bytes).decode()


def decrypt_provider_config(encrypted_config: str) -> dict[str, Any]:
    """
    Decrypt email provider configuration.

    Args:
        encrypted_config: Base64 encoded encrypted string

    Returns:
        Decrypted provider configuration dictionary
    """
    encrypted_bytes = base64.urlsafe_b64decode(encrypted_config.encode())
    decrypted_bytes = _fernet.decrypt(encrypted_bytes)
    return json.loads(decrypted_bytes.decode())


def encrypt_provider_configs(
    provider_configs: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Encrypt sensitive fields in a list of provider configurations.

    Args:
        provider_configs: List of provider configuration dictionaries

    Returns:
        List of configurations with sensitive fields encrypted
    """
    # Fields that should be encrypted
    sensitive_fields = {"password", "api_key", "secret", "token", "auth_key"}

    encrypted_configs = []
    for config in provider_configs:
        encrypted_config = config.copy()

        # Encrypt sensitive fields
        for field, value in config.items():
            if field.lower() in sensitive_fields and value:
                encrypted_config[field] = encrypt_provider_config({field: value})

        encrypted_configs.append(encrypted_config)

    return encrypted_configs


def decrypt_provider_configs(
    provider_configs: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Decrypt sensitive fields in a list of provider configurations.

    Args:
        provider_configs: List of provider configuration dictionaries with encrypted fields

    Returns:
        List of configurations with sensitive fields decrypted
    """
    # Fields that should be decrypted
    sensitive_fields = {"password", "api_key", "secret", "token", "auth_key"}

    decrypted_configs = []
    for config in provider_configs:
        decrypted_config = config.copy()

        # Decrypt sensitive fields
        for field, value in config.items():
            if field.lower() in sensitive_fields and value:
                decrypted_value = decrypt_provider_config(value)
                decrypted_config[field] = decrypted_value[field]

        decrypted_configs.append(decrypted_config)

    return decrypted_configs
