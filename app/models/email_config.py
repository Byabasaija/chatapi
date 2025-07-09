from enum import Enum


class EmailProviderType(str, Enum):
    """Email provider types supported by the system."""

    SMTP = "smtp"
    MAILGUN = "mailgun"
