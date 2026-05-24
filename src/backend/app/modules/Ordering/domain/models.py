import uuid
import datetime
from sqlalchemy import Column, String, DateTime, Numeric, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.infrastructure import Base

class BillSession(Base):
    """Represents a dynamic table billing session (adisyon). Only one active per table."""
    __tablename__ = "bill_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    table_id = Column(UUID(as_uuid=True), nullable=False)
    status = Column(String(20), nullable=False, default="open") # open, closing, closed, reopened, cancelled
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.datetime.now(datetime.timezone.utc))
    updated_at = Column(DateTime, nullable=False, default=lambda: datetime.datetime.now(datetime.timezone.utc), onupdate=lambda: datetime.datetime.now(datetime.timezone.utc))

    orders = relationship("Order", back_populates="bill_session", cascade="all, delete-orphan")
    manual_payments = relationship("ManualPayment", back_populates="bill_session", cascade="all, delete-orphan")
    reopen_events = relationship("BillReopenEvent", back_populates="bill_session", cascade="all, delete-orphan")

class Order(Base):
    """Represents a customer order consisting of multiple ordered menu items."""
    __tablename__ = "orders"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    bill_session_id = Column(UUID(as_uuid=True), ForeignKey("bill_sessions.id", ondelete="CASCADE"), nullable=False)
    order_number = Column(String(50), nullable=False, unique=True)
    status = Column(String(20), nullable=False, default="submitted") # submitted, preparing, ready, served, voided
    total_amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(5), nullable=False, default="TRY")
    submitted_at_utc = Column(DateTime, nullable=False, default=lambda: datetime.datetime.now(datetime.timezone.utc))

    bill_session = relationship("BillSession", back_populates="orders")
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    station_tickets = relationship("StationTicket", back_populates="order", cascade="all, delete-orphan")

class OrderItem(Base):
    """Detailed ordered item persisted in a snapshot format."""
    __tablename__ = "order_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id", ondelete="CASCADE"), nullable=False)
    menu_item_id = Column(UUID(as_uuid=True), nullable=False)
    name = Column(String(150), nullable=False)
    price = Column(Numeric(10, 2), nullable=False)
    quantity = Column(Integer, nullable=False)
    note = Column(String(255), nullable=True)

    order = relationship("Order", back_populates="items")

class StationTicket(Base):
    """A sub-ticket routed to a specific prep station (kitchen, bar etc.) for production control."""
    __tablename__ = "station_tickets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id", ondelete="CASCADE"), nullable=False)
    station_code = Column(String(50), nullable=False)
    status = Column(String(20), nullable=False, default="pending") # pending, preparing, ready, completed, cancelled
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.datetime.now(datetime.timezone.utc))

    order = relationship("Order", back_populates="station_tickets")
    items = relationship("StationTicketItem", back_populates="station_ticket", cascade="all, delete-orphan")

class StationTicketItem(Base):
    """Detailed preparation items linked to a prep ticket."""
    __tablename__ = "station_ticket_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    station_ticket_id = Column(UUID(as_uuid=True), ForeignKey("station_tickets.id", ondelete="CASCADE"), nullable=False)
    menu_item_id = Column(UUID(as_uuid=True), nullable=False)
    name = Column(String(150), nullable=False)
    quantity = Column(Integer, nullable=False)
    note = Column(String(255), nullable=True)

    station_ticket = relationship("StationTicket", back_populates="items")

class ManualPayment(Base):
    """Represents an external/offline manual payment recorded by staff for audit and closure."""
    __tablename__ = "manual_payments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    bill_session_id = Column(UUID(as_uuid=True), ForeignKey("bill_sessions.id", ondelete="CASCADE"), nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(5), nullable=False, default="TRY")
    payment_method = Column(String(30), nullable=False) # cash, card_external_pos, bank_transfer, other
    status = Column(String(20), nullable=False, default="completed")
    external_reference = Column(String(100), nullable=True)
    note = Column(String(255), nullable=True)
    recorded_at_utc = Column(DateTime, nullable=False, default=lambda: datetime.datetime.now(datetime.timezone.utc))

    bill_session = relationship("BillSession", back_populates="manual_payments")

class BillReopenEvent(Base):
    """Represents a historic log of an authorized reopening of a closed bill session."""
    __tablename__ = "bill_reopen_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    bill_session_id = Column(UUID(as_uuid=True), ForeignKey("bill_sessions.id", ondelete="CASCADE"), nullable=False)
    reason = Column(String(255), nullable=False)
    reopened_by = Column(String(100), nullable=False)
    reopened_at_utc = Column(DateTime, nullable=False, default=lambda: datetime.datetime.now(datetime.timezone.utc))

    bill_session = relationship("BillSession", back_populates="reopen_events")
