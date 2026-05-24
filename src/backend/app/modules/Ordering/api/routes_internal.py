import uuid
from typing import Optional, List
from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel, Field
from decimal import Decimal
from app.core.api import create_problem_response
from app.modules.CustomerAccess.api.routes import get_tenant_slug
from app.modules.Ordering.application.services import OrderingService

router = APIRouter(tags=["Staff Billing & Payments"])

# --- SECURITY DEPENDENCY ---

def require_staff_permission(required_perm: str):
    def dependency(x_staff_permissions: Optional[str] = Header(None, alias="X-Staff-Permissions")):
        if not x_staff_permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Staff permissions header missing."
            )
        
        perms = [p.strip() for p in x_staff_permissions.split(",")]
        if required_perm not in perms:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing required permission: {required_perm}"
            )
        return x_staff_permissions
    return dependency

# --- SCHEMAS ---

class RecordManualPaymentRequest(BaseModel):
    amount: float = Field(..., gt=0, description="Pozitif ödeme tutarı.")
    currency: str = Field("TRY", description="Para birimi, adisyon para birimiyle eşleşmelidir.")
    payment_method: str = Field(..., description="cash, card_external_pos, bank_transfer veya other")
    external_reference: Optional[str] = Field(None, description="Harici referans numarası.")
    note: Optional[str] = Field(None, description="Opsiyonel not.")

class ManualPaymentResponse(BaseModel):
    manual_payment_id: uuid.UUID
    bill_session_id: uuid.UUID
    amount: float
    currency: str
    payment_method: str
    status: str
    recorded_at_utc: str

class CloseBillSessionRequest(BaseModel):
    manual_payment: Optional[RecordManualPaymentRequest] = None
    reason: Optional[str] = None

class ReopenBillSessionRequest(BaseModel):
    reason: str = Field(..., min_length=1, description="Adisyonun geri açılma gerekçesi boş olamaz.")

class BillOrderItemDetail(BaseModel):
    menu_item_id: uuid.UUID
    name: str
    price: float
    quantity: int
    note: Optional[str]

class BillOrderDetail(BaseModel):
    order_id: uuid.UUID
    order_number: str
    status: str
    total_amount: float
    submitted_at_utc: str
    items: List[BillOrderItemDetail]

class ManualPaymentDetail(BaseModel):
    id: uuid.UUID
    amount: float
    currency: str
    payment_method: str
    status: str
    recorded_at_utc: str

class ReopenEventDetail(BaseModel):
    id: uuid.UUID
    reason: str
    reopened_by: str
    reopened_at_utc: str

class BillSessionDetailResponse(BaseModel):
    bill_session_id: uuid.UUID
    table_id: uuid.UUID
    status: str
    attached_orders: List[BillOrderDetail]
    manual_payments: List[ManualPaymentDetail]
    reopen_events: List[ReopenEventDetail]
    total_amount: float
    currency: str

# --- ROUTES ---

@router.get("/api/internal/bills/{billSessionId}", response_model=BillSessionDetailResponse)
def get_bill_detail(
    billSessionId: uuid.UUID,
    tenant_slug: str = Depends(get_tenant_slug),
    _: str = Depends(require_staff_permission("tenant.bills.view"))
):
    """Retrieves cashier bill detail including attached orders, manual payments, and reopen logs."""
    try:
        bill = OrderingService.get_bill_session_detail(tenant_slug, billSessionId)
    except ValueError as e:
        return create_problem_response(
            status_code=status.HTTP_404_NOT_FOUND,
            title="Adisyon Bulunamadı",
            detail=str(e),
            error_code="BILL_NOT_FOUND",
            instance=f"/api/internal/bills/{billSessionId}"
        )

    # Convert to response format
    attached_orders = []
    bill_total = Decimal("0.00")
    for ord in bill.orders:
        if ord.status == "voided":
            continue
        bill_total += ord.total_amount
        
        items = []
        for item in ord.items:
            items.append(BillOrderItemDetail(
                menu_item_id=item.menu_item_id,
                name=item.name,
                price=float(item.price),
                quantity=item.quantity,
                note=item.note
            ))
            
        attached_orders.append(BillOrderDetail(
            order_id=ord.id,
            order_number=ord.order_number,
            status=ord.status,
            total_amount=float(ord.total_amount),
            submitted_at_utc=ord.submitted_at_utc.isoformat(),
            items=items
        ))

    payments = []
    for pay in bill.manual_payments:
        payments.append(ManualPaymentDetail(
            id=pay.id,
            amount=float(pay.amount),
            currency=pay.currency,
            payment_method=pay.payment_method,
            status=pay.status,
            recorded_at_utc=pay.recorded_at_utc.isoformat()
        ))

    reopens = []
    for event in bill.reopen_events:
        reopens.append(ReopenEventDetail(
            id=event.id,
            reason=event.reason,
            reopened_by=event.reopened_by,
            reopened_at_utc=event.reopened_at_utc.isoformat()
        ))

    return BillSessionDetailResponse(
        bill_session_id=bill.id,
        table_id=bill.table_id,
        status=bill.status,
        attached_orders=attached_orders,
        manual_payments=payments,
        reopen_events=reopens,
        total_amount=float(bill_total),
        currency="TRY"
    )

@router.post("/api/internal/bills/{billSessionId}/manual-payments", response_model=ManualPaymentResponse)
def record_manual_payment(
    billSessionId: uuid.UUID,
    payload: RecordManualPaymentRequest,
    tenant_slug: str = Depends(get_tenant_slug),
    _: str = Depends(require_staff_permission("tenant.manual_payments.record"))
):
    """Records an external manual/offline payment for a bill session."""
    if payload.payment_method not in ("cash", "card_external_pos", "bank_transfer", "other"):
        return create_problem_response(
            status_code=status.HTTP_400_BAD_REQUEST,
            title="Geçersiz Ödeme Yöntemi",
            detail="Ödeme yöntemi cash, card_external_pos, bank_transfer veya other olmalıdır.",
            error_code="INVALID_PAYMENT_METHOD",
            instance=f"/api/internal/bills/{billSessionId}/manual-payments"
        )

    try:
        payment = OrderingService.record_manual_payment(
            tenant_slug=tenant_slug,
            bill_session_id=billSessionId,
            amount=Decimal(str(payload.amount)),
            currency=payload.currency,
            payment_method=payload.payment_method,
            external_reference=payload.external_reference,
            note=payload.note
        )
    except ValueError as e:
        return create_problem_response(
            status_code=status.HTTP_400_BAD_REQUEST,
            title="Ödeme Kaydedilemedi",
            detail=str(e),
            error_code="MANUAL_PAYMENT_FAILED",
            instance=f"/api/internal/bills/{billSessionId}/manual-payments"
        )

    return ManualPaymentResponse(
        manual_payment_id=payment.id,
        bill_session_id=payment.bill_session_id,
        amount=float(payment.amount),
        currency=payment.currency,
        payment_method=payment.payment_method,
        status=payment.status,
        recorded_at_utc=payment.recorded_at_utc.isoformat()
    )

@router.post("/api/internal/bills/{billSessionId}/close", response_model=BillSessionDetailResponse)
def close_bill_session(
    billSessionId: uuid.UUID,
    payload: CloseBillSessionRequest,
    tenant_slug: str = Depends(get_tenant_slug),
    x_staff_permissions: str = Depends(require_staff_permission("tenant.bills.close"))
):
    """Closes the bill session, recalculating the total and checking matching manual payments."""
    # Ensure staff also has permission to record payments if they provide manual_payment
    if payload.manual_payment:
        perms = [p.strip() for p in x_staff_permissions.split(",")]
        if "tenant.manual_payments.record" not in perms:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Missing required permission to record manual payments: tenant.manual_payments.record"
            )

    pay_payload = None
    if payload.manual_payment:
        pay_payload = payload.manual_payment.model_dump()

    try:
        bill = OrderingService.close_bill_session(
            tenant_slug=tenant_slug,
            bill_session_id=billSessionId,
            manual_payment_payload=pay_payload,
            reason=payload.reason
        )
    except ValueError as e:
        return create_problem_response(
            status_code=status.HTTP_400_BAD_REQUEST,
            title="Adisyon Kapatılamadı",
            detail=str(e),
            error_code="BILL_CLOSE_FAILED",
            instance=f"/api/internal/bills/{billSessionId}/close"
        )

    # Convert to response format
    attached_orders = []
    bill_total = Decimal("0.00")
    for ord in bill.orders:
        if ord.status == "voided":
            continue
        bill_total += ord.total_amount
        
        items = []
        for item in ord.items:
            items.append(BillOrderItemDetail(
                menu_item_id=item.menu_item_id,
                name=item.name,
                price=float(item.price),
                quantity=item.quantity,
                note=item.note
            ))
            
        attached_orders.append(BillOrderDetail(
            order_id=ord.id,
            order_number=ord.order_number,
            status=ord.status,
            total_amount=float(ord.total_amount),
            submitted_at_utc=ord.submitted_at_utc.isoformat(),
            items=items
        ))

    payments = []
    for pay in bill.manual_payments:
        payments.append(ManualPaymentDetail(
            id=pay.id,
            amount=float(pay.amount),
            currency=pay.currency,
            payment_method=pay.payment_method,
            status=pay.status,
            recorded_at_utc=pay.recorded_at_utc.isoformat()
        ))

    reopens = []
    for event in bill.reopen_events:
        reopens.append(ReopenEventDetail(
            id=event.id,
            reason=event.reason,
            reopened_by=event.reopened_by,
            reopened_at_utc=event.reopened_at_utc.isoformat()
        ))

    return BillSessionDetailResponse(
        bill_session_id=bill.id,
        table_id=bill.table_id,
        status=bill.status,
        attached_orders=attached_orders,
        manual_payments=payments,
        reopen_events=reopens,
        total_amount=float(bill_total),
        currency="TRY"
    )

@router.post("/api/internal/bills/{billSessionId}/reopen", response_model=BillSessionDetailResponse)
def reopen_bill_session(
    billSessionId: uuid.UUID,
    payload: ReopenBillSessionRequest,
    tenant_slug: str = Depends(get_tenant_slug),
    _: str = Depends(require_staff_permission("tenant.bills.reopen"))
):
    """Reopens a closed bill session logging the required authorization reason."""
    try:
        bill = OrderingService.reopen_bill_session(
            tenant_slug=tenant_slug,
            bill_session_id=billSessionId,
            reason=payload.reason,
            reopened_by="manager" # Simulated role based on token/permission validation
        )
    except ValueError as e:
        return create_problem_response(
            status_code=status.HTTP_400_BAD_REQUEST,
            title="Adisyon Geri Açılamadı",
            detail=str(e),
            error_code="BILL_REOPEN_FAILED",
            instance=f"/api/internal/bills/{billSessionId}/reopen"
        )

    # Convert to response format
    attached_orders = []
    bill_total = Decimal("0.00")
    for ord in bill.orders:
        if ord.status == "voided":
            continue
        bill_total += ord.total_amount
        
        items = []
        for item in ord.items:
            items.append(BillOrderItemDetail(
                menu_item_id=item.menu_item_id,
                name=item.name,
                price=float(item.price),
                quantity=item.quantity,
                note=item.note
            ))
            
        attached_orders.append(BillOrderDetail(
            order_id=ord.id,
            order_number=ord.order_number,
            status=ord.status,
            total_amount=float(ord.total_amount),
            submitted_at_utc=ord.submitted_at_utc.isoformat(),
            items=items
        ))

    payments = []
    for pay in bill.manual_payments:
        payments.append(ManualPaymentDetail(
            id=pay.id,
            amount=float(pay.amount),
            currency=pay.currency,
            payment_method=pay.payment_method,
            status=pay.status,
            recorded_at_utc=pay.recorded_at_utc.isoformat()
        ))

    reopens = []
    for event in bill.reopen_events:
        reopens.append(ReopenEventDetail(
            id=event.id,
            reason=event.reason,
            reopened_by=event.reopened_by,
            reopened_at_utc=event.reopened_at_utc.isoformat()
        ))

    return BillSessionDetailResponse(
        bill_session_id=bill.id,
        table_id=bill.table_id,
        status=bill.status,
        attached_orders=attached_orders,
        manual_payments=payments,
        reopen_events=reopens,
        total_amount=float(bill_total),
        currency="TRY"
    )

class TableStatusResponse(BaseModel):
    id: uuid.UUID
    name: str
    capacity: int
    status: str
    bill: float
    bill_session_id: Optional[uuid.UUID]

@router.get("/api/internal/tables", response_model=List[TableStatusResponse])
def list_tables(
    tenant_slug: str = Depends(get_tenant_slug),
    _: str = Depends(require_staff_permission("tenant.bills.view"))
):
    """Lists all tables with their active bills and status states for the personnel grid."""
    from app.modules.Tables.infrastructure.persistence import TableRepository
    from app.modules.Ordering.infrastructure.persistence import BillSessionRepository
    
    with session_manager.tenant_session(tenant_slug) as session:
        db_tables = TableRepository.list_all(session)
        table_statuses = []
        for table in db_tables:
            active_bill = BillSessionRepository.get_active_by_table(session, table.id)
            bill_amount = 0.0
            status_str = "Boş"
            bill_session_id = None
            
            if active_bill:
                status_str = "Dolu"
                bill_session_id = active_bill.id
                active_orders = [ord for ord in active_bill.orders if ord.status != "voided"]
                bill_amount = float(sum(ord.total_amount for ord in active_orders))
                
            table_statuses.append(TableStatusResponse(
                id=table.id,
                name=table.table_number,
                capacity=4,
                status=status_str,
                bill=bill_amount,
                bill_session_id=bill_session_id
            ))
        return table_statuses

class StaffOrderItemResponse(BaseModel):
    name: str
    quantity: int

class StaffOrderResponse(BaseModel):
    id: uuid.UUID
    table: str
    items: List[StaffOrderItemResponse]
    total: float
    time: str
    status: str

@router.get("/api/internal/orders", response_model=List[StaffOrderResponse])
def list_active_orders(
    tenant_slug: str = Depends(get_tenant_slug),
    _: str = Depends(require_staff_permission("tenant.bills.view"))
):
    """Lists all active orders for the kitchen queue screen."""
    import datetime
    from app.modules.Ordering.domain.models import Order
    from app.modules.Tables.infrastructure.persistence import TableRepository
    
    with session_manager.tenant_session(tenant_slug) as session:
        db_orders = session.query(Order).filter(Order.status.in_(["submitted", "preparing", "ready"])).order_by(Order.submitted_at_utc.asc()).all()
        db_tables = TableRepository.list_all(session)
        table_map = {table.id: table.table_number for table in db_tables}
        
        orders_list = []
        for ord in db_orders:
            table_number = table_map.get(ord.bill_session.table_id) if ord.bill_session else "Bilinmeyen Masa"
            items = [StaffOrderItemResponse(name=item.name, quantity=item.quantity) for item in ord.items]
            
            status_map = {
                "submitted": "Sırada",
                "preparing": "Hazırlanıyor",
                "ready": "Mutfakta Hazır"
            }
            status_str = status_map.get(ord.status, "Sırada")
            
            time_str = "Yeni"
            if ord.submitted_at_utc:
                diff = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None) - ord.submitted_at_utc
                mins = int(diff.total_seconds() / 60)
                time_str = f"{mins} dakika önce" if mins > 0 else "Yeni"
                
            orders_list.append(StaffOrderResponse(
                id=ord.id,
                table=table_number,
                items=items,
                total=float(ord.total_amount),
                time=time_str,
                status=status_str
            ))
        return orders_list

class UpdateOrderStatusRequest(BaseModel):
    status: str

@router.post("/api/internal/orders/{orderId}/status", response_model=StaffOrderResponse)
def update_order_status(
    orderId: uuid.UUID,
    payload: UpdateOrderStatusRequest,
    tenant_slug: str = Depends(get_tenant_slug),
    _: str = Depends(require_staff_permission("tenant.bills.view"))
):
    """Updates the status of an order (e.g. prepared, preparing etc.) in the kitchen."""
    from app.modules.Ordering.domain.models import Order
    from app.modules.Tables.infrastructure.persistence import TableRepository
    
    with session_manager.tenant_session(tenant_slug) as session:
        ord = session.query(Order).filter(Order.id == orderId).first()
        if not ord:
            raise HTTPException(status_code=404, detail="Sipariş bulunamadı.")
            
        ord.status = payload.status
        session.add(ord)
        session.commit()
        
        db_tables = TableRepository.list_all(session)
        table_map = {table.id: table.table_number for table in db_tables}
        table_number = table_map.get(ord.bill_session.table_id) if ord.bill_session else "Bilinmeyen Masa"
        items = [StaffOrderItemResponse(name=item.name, quantity=item.quantity) for item in ord.items]
        
        status_map = {
            "submitted": "Sırada",
            "preparing": "Hazırlanıyor",
            "ready": "Mutfakta Hazır",
            "served": "Teslim Edildi"
        }
        status_str = status_map.get(ord.status, ord.status)
        
        return StaffOrderResponse(
            id=ord.id,
            table=table_number,
            items=items,
            total=float(ord.total_amount),
            time="Güncellendi",
            status=status_str
        )
