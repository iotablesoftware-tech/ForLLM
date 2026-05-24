import uuid
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from app.modules.Ordering.domain.models import BillSession, Order, ManualPayment, BillReopenEvent

class BillSessionRepository:
    @staticmethod
    def add(session: Session, bill_session: BillSession) -> None:
        session.add(bill_session)

    @staticmethod
    def get_by_id(session: Session, bill_session_id: uuid.UUID) -> Optional[BillSession]:
        return session.query(BillSession).filter(BillSession.id == bill_session_id).first()

    @staticmethod
    def get_by_id_for_update(session: Session, bill_session_id: uuid.UUID) -> Optional[BillSession]:
        return session.query(BillSession).filter(BillSession.id == bill_session_id).with_for_update().first()

    @staticmethod
    def get_active_by_table(session: Session, table_id: uuid.UUID) -> Optional[BillSession]:
        # open or reopened bill sessions are active
        return session.query(BillSession).filter(
            and_(
                BillSession.table_id == table_id,
                or_(
                    BillSession.status == "open",
                    BillSession.status == "reopened"
                )
            )
        ).order_by(BillSession.created_at.desc()).first()

class OrderRepository:
    @staticmethod
    def add(session: Session, order: Order) -> None:
        session.add(order)

    @staticmethod
    def get_by_id(session: Session, order_id: uuid.UUID) -> Optional[Order]:
        return session.query(Order).filter(Order.id == order_id).first()

    @staticmethod
    def list_by_bill_session(session: Session, bill_session_id: uuid.UUID) -> List[Order]:
        return session.query(Order).filter(Order.bill_session_id == bill_session_id).order_by(Order.submitted_at_utc.asc()).all()

class ManualPaymentRepository:
    @staticmethod
    def add(session: Session, payment: ManualPayment) -> None:
        session.add(payment)

    @staticmethod
    def list_by_bill_session(session: Session, bill_session_id: uuid.UUID) -> List[ManualPayment]:
        return session.query(ManualPayment).filter(ManualPayment.bill_session_id == bill_session_id).all()

class BillReopenEventRepository:
    @staticmethod
    def add(session: Session, event: BillReopenEvent) -> None:
        session.add(event)
