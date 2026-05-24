from typing import Optional
from sqlalchemy.orm import Session
from app.modules.Tenancy.domain.models import RestaurantProfile, TenantSettings

class RestaurantProfileRepository:
    """Transactional persistence operations for RestaurantProfile entities."""
    @staticmethod
    def get(session: Session) -> Optional[RestaurantProfile]:
        # There should only be one profile record per tenant database
        return session.query(RestaurantProfile).first()

    @staticmethod
    def add(session: Session, profile: RestaurantProfile) -> None:
        session.add(profile)

class TenantSettingsRepository:
    """Transactional persistence operations for TenantSettings entities."""
    @staticmethod
    def get(session: Session) -> Optional[TenantSettings]:
        # There should only be one settings record per tenant database
        return session.query(TenantSettings).first()

    @staticmethod
    def add(session: Session, settings: TenantSettings) -> None:
        session.add(settings)
