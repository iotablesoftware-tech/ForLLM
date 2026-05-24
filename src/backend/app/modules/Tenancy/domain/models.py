import uuid
from sqlalchemy import Column, String, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from app.core.infrastructure import Base

class RestaurantProfile(Base):
    """Stores operational profile details for a specific tenant inside their isolated database."""
    __tablename__ = "restaurant_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    default_locale = Column(String(10), nullable=False, default="tr-TR")
    default_currency = Column(String(5), nullable=False, default="TRY")
    timezone = Column(String(50), nullable=False, default="Europe/Istanbul")

class TenantSettings(Base):
    """Stores feature flags and operational configurations for a specific tenant inside their isolated database."""
    __tablename__ = "tenant_settings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    self_ordering_active = Column(Boolean, nullable=False, default=True)
    station_acceptance_required = Column(Boolean, nullable=False, default=True)
