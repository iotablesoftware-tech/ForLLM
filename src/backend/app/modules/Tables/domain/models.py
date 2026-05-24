import uuid
from sqlalchemy import Column, String, DateTime
from sqlalchemy.dialects.postgresql import UUID
from app.core.infrastructure import Base

class Table(Base):
    """Represents a physical table in a restaurant. Its state and QR code are managed server-side."""
    __tablename__ = "tables"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    table_number = Column(String(50), nullable=False, unique=True)
    status = Column(String(20), nullable=False, default="active") # active, closed, restricted
    qr_token = Column(String(255), nullable=True)
    qr_expires_at = Column(DateTime, nullable=True)
