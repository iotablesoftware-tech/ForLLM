import uuid
from sqlalchemy import Column, String, Numeric, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from app.core.infrastructure import Base

class MenuCategory(Base):
    """Represents a category (e.g. Appetizers, Mains, Drinks) in a restaurant's menu."""
    __tablename__ = "menu_categories"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    display_order = Column(Integer, nullable=False, default=0)

class MenuItem(Base):
    """Represents an orderable product in the restaurant's menu catalog."""
    __tablename__ = "menu_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(150), nullable=False)
    price = Column(Numeric(10, 2), nullable=False) # Precision 10, scale 2 (kuruş accuracy)
    status = Column(String(20), nullable=False, default="active") # active, out_of_stock, inactive
    category_id = Column(UUID(as_uuid=True), ForeignKey("menu_categories.id"), nullable=True)
    station_code = Column(String(50), nullable=False) # Maps to Station.code for routing
