from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base_class import Base


class ClientEmailConfig(Base):
    """
    Client-specific email configuration for SMTP settings.
    Allows each client to configure their own SMTP provider for transactional emails.
    """

    __tablename__ = "client_email_configs"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(
        String, ForeignKey("clients.id"), nullable=False, index=True, unique=True
    )

    # SMTP Configuration
    smtp_host = Column(String, nullable=False)
    smtp_port = Column(Integer, nullable=False, default=587)
    smtp_user = Column(String, nullable=False)
    smtp_password = Column(String, nullable=False)  # Should be encrypted in production
    smtp_use_tls = Column(Boolean, nullable=False, default=True)
    smtp_use_ssl = Column(Boolean, nullable=False, default=False)

    # Default sender configuration
    default_from_email = Column(String, nullable=False)
    default_from_name = Column(String, nullable=True)
    default_reply_to = Column(String, nullable=True)

    # Configuration metadata
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(
        Boolean, default=False, nullable=False
    )  # Email verification status
    verification_token = Column(String, nullable=True)  # For SMTP verification
    last_verified_at = Column(DateTime(timezone=True), nullable=True)

    # Rate limiting and quotas
    daily_send_limit = Column(Integer, nullable=True)  # Max emails per day
    hourly_send_limit = Column(Integer, nullable=True)  # Max emails per hour

    # Tracking
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Notes and configuration details
    notes = Column(Text, nullable=True)  # Admin notes about the configuration

    # Relationships
    client = relationship("Client", back_populates="email_configs")


class EmailSendingStats(Base):
    """
    Track email sending statistics per client to enforce rate limits and quotas.
    """

    __tablename__ = "email_sending_stats"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(String, nullable=False, index=True)
    date = Column(DateTime(timezone=True), nullable=False, index=True)

    # Counters
    emails_sent = Column(Integer, default=0, nullable=False)
    emails_failed = Column(Integer, default=0, nullable=False)
    emails_bounced = Column(Integer, default=0, nullable=False)

    # Provider breakdown
    smtp_sent = Column(Integer, default=0, nullable=False)
    mailgun_sent = Column(Integer, default=0, nullable=False)

    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class EmailTemplate(Base):
    """
    Reusable email templates for clients.
    Supports variable substitution and different template types.
    """

    __tablename__ = "email_templates"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(String, nullable=False, index=True)

    # Template identification
    template_name = Column(
        String, nullable=False
    )  # e.g., "welcome_email", "password_reset"
    template_type = Column(
        String, nullable=False
    )  # "transactional", "marketing", "system"

    # Email content
    subject = Column(String, nullable=False)
    html_content = Column(Text, nullable=True)  # HTML version
    text_content = Column(Text, nullable=True)  # Plain text version

    # Template metadata
    is_active = Column(Boolean, default=True, nullable=False)
    version = Column(Integer, default=1, nullable=False)

    # Variable placeholders documentation
    variables = Column(Text, nullable=True)  # JSON string of available variables

    # Usage tracking
    usage_count = Column(Integer, default=0, nullable=False)
    last_used_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
