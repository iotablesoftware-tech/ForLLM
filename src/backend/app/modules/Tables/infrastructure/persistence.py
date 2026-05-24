from typing import List, Optional
import uuid
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.modules.Tables.domain.models import Table

class TableRepository:
    """Transactional persistence operations for Table entities."""
    @staticmethod
    def get_by_id(session: Session, table_id: uuid.UUID) -> Optional[Table]:
        return session.get(Table, table_id)

    @staticmethod
    def get_by_number(session: Session, table_number: str) -> Optional[Table]:
        stmt = select(Table).where(Table.table_number == table_number)
        return session.execute(stmt).scalar_one_or_none()

    @staticmethod
    def add(session: Session, table: Table) -> None:
        session.add(table)

    @staticmethod
    def list_all(session: Session) -> List[Table]:
        stmt = select(Table).order_by(Table.table_number)
        return list(session.execute(stmt).scalars().all())
