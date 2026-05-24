from typing import List, Optional
import uuid
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.modules.Stations.domain.models import Station

class StationRepository:
    """Transactional persistence operations for Station entities."""
    @staticmethod
    def get_by_id(session: Session, station_id: uuid.UUID) -> Optional[Station]:
        return session.get(Station, station_id)

    @staticmethod
    def get_by_code(session: Session, code: str) -> Optional[Station]:
        stmt = select(Station).where(Station.code == code)
        return session.execute(stmt).scalar_one_or_none()

    @staticmethod
    def add(session: Session, station: Station) -> None:
        session.add(station)

    @staticmethod
    def list_all(session: Session) -> List[Station]:
        stmt = select(Station).order_by(Station.code)
        return list(session.execute(stmt).scalars().all())
