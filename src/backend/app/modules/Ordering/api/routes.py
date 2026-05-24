import uuid
import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, Request, Response, status
from pydantic import BaseModel, Field
from decimal import Decimal
from app.core.api import create_problem_response
from app.modules.CustomerAccess.api.routes import get_tenant_slug, get_active_customer_session
from app.modules.CustomerAccess.domain.models import CustomerSession
from app.modules.Ordering.application.services import OrderingService

router = APIRouter(tags=["Customer Ordering"])

# --- SCHEMAS ---

class SubmitCustomerOrderRequest(BaseModel):
    expected_version: int = Field(..., description="Sepet üzerinde en son görülen versiyon.")
    client_note: Optional[str] = Field(None, description="Siparişle ilgili genel istemci notu.")

class SubmitCustomerOrderResponse(BaseModel):
    order_id: uuid.UUID
    order_number: str
    status: str
    submitted_at_utc: datetime.datetime
    total_amount: float
    currency: str
    station_ticket_count: int
    session_status: str = "offline"

class CustomerBillItemResponse(BaseModel):
    menu_item_id: str
    name: str
    price: float
    quantity: int
    note: Optional[str]

class CustomerBillOrderResponse(BaseModel):
    order_id: str
    order_number: str
    status: str
    total_amount: float
    submitted_at_utc: str
    items: List[CustomerBillItemResponse]

class CustomerBillResponse(BaseModel):
    bill_session_id: Optional[str]
    status: str
    total_amount: float
    orders: List[CustomerBillOrderResponse]

# --- ROUTES ---

@router.post("/orders/submit", response_model=SubmitCustomerOrderResponse)
def submit_order(
    payload: SubmitCustomerOrderRequest,
    response: Response,
    tenant_slug: str = Depends(get_tenant_slug),
    active_session: CustomerSession = Depends(get_active_customer_session)
):
    """Submits the collaborative table cart as exactly one order and moves the customer session offline."""
    try:
        order = OrderingService.submit_order(
            tenant_slug=tenant_slug,
            session_id=active_session.id,
            expected_cart_version=payload.expected_version,
            client_note=payload.client_note
        )
    except ValueError as e:
        err_msg = str(e)
        if err_msg == "CART_STATE_OUTOFDATE":
            return create_problem_response(
                status_code=status.HTTP_409_CONFLICT,
                title="Sepet Versiyon Çakışması",
                detail="Sepet başka bir kullanıcı tarafından değiştirilmiş. Lütfen yenileyip tekrar deneyin.",
                error_code="CART_STATE_OUTOFDATE",
                instance="/orders/submit"
            )
        return create_problem_response(
            status_code=status.HTTP_400_BAD_REQUEST,
            title="Sipariş Gönderilemedi",
            detail=err_msg,
            error_code="ORDER_SUBMISSION_FAILED",
            instance="/orders/submit"
        )

    # Oturum offline'a çekildiğinden çerezi de temizliyoruz
    response.delete_cookie("customer_session")

    return SubmitCustomerOrderResponse(
        order_id=order.id,
        order_number=order.order_number,
        status=order.status,
        submitted_at_utc=order.submitted_at_utc_day if hasattr(order, 'submitted_at_utc_day') else order.submitted_at_utc,
        total_amount=float(order.total_amount),
        currency=order.currency,
        station_ticket_count=len(order.station_tickets),
        session_status="offline"
    )

@router.get("/bill/current", response_model=CustomerBillResponse)
def get_current_bill(
    tenant_slug: str = Depends(get_tenant_slug),
    active_session: CustomerSession = Depends(get_active_customer_session)
):
    """Returns the current open bill/adisyon summary for the dynamic customer table."""
    try:
        bill_summary = OrderingService.get_current_bill_summary(tenant_slug, active_session.id)
    except ValueError as e:
        return create_problem_response(
            status_code=status.HTTP_400_BAD_REQUEST,
            title="Adisyon Görüntülenemedi",
            detail=str(e),
            error_code="BILL_VIEW_FAILED",
            instance="/bill/current"
        )

    return CustomerBillResponse(
        bill_session_id=bill_summary["bill_session_id"],
        status=bill_summary["status"],
        total_amount=bill_summary["total_amount"],
        orders=bill_summary["orders"]
    )
