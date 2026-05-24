import uuid
import datetime
from sqlalchemy import Column, String, DateTime, Integer
from sqlalchemy.dialects.postgresql import UUID
from app.core.infrastructure import Base

class CustomerSession(Base):
    """Represents a short-lived customer ordering session linked to a physical restaurant table."""
    __tablename__ = "customer_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_slug = Column(String(100), nullable=False)
    table_id = Column(UUID(as_uuid=True), nullable=False)
    status = Column(String(20), nullable=False, default="active") # active, submitted, offline, expired
    expires_at_utc = Column(DateTime, nullable=False)
    extension_count = Column(Integer, nullable=False, default=0)
    max_extensions = Column(Integer, nullable=False, default=3)
    max_expires_at_utc = Column(DateTime, nullable=False)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.datetime.now(datetime.timezone.utc))
    updated_at = Column(DateTime, nullable=False, default=lambda: datetime.datetime.now(datetime.timezone.utc), onupdate=lambda: datetime.datetime.now(datetime.timezone.utc))
