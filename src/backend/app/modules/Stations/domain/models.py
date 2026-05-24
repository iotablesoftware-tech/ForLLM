import uuid
from sqlalchemy import Column, String
from sqlalchemy.dialects.postgresql import UUID
from app.core.infrastructure import Base

class Station(Base):
    """Represents a preparation station (e.g. Kitchen, Bar) in a restaurant."""
    __tablename__ = "stations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code = Column(String(50), nullable=False, unique=True) # e.g. "kitchen_main", "bar_beverages"
    name = Column(String(100), nullable=False)
    status = Column(String(20), nullable=False, default="active") # active, inactive
