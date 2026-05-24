import uuid
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, text
import datetime
from app.modules.CustomerAccess.domain.models import CustomerSession

class CustomerSessionRepository:
    @staticmethod
    def add(session: Session, customer_session: CustomerSession) -> None:
        session.add(customer_session)

    @staticmethod
    def get_by_id(session: Session, session_id: uuid.UUID) -> Optional[CustomerSession]:
        return session.query(CustomerSession).filter(CustomerSession.id == session_id).first()

    @staticmethod
    def get_active_by_table(session: Session, table_id: uuid.UUID) -> Optional[CustomerSession]:
        now = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)
        # Check active session that has not expired
        return session.query(CustomerSession).filter(
            and_(
                CustomerSession.table_id == table_id,
                CustomerSession.status == "active",
                CustomerSession.expires_at_utc > now
            )
        ).order_by(CustomerSession.expires_at_utc.desc()).first()
