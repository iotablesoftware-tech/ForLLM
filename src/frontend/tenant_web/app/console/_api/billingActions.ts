"use server";

import { backendFetch, handleApiResponse } from "../../../lib/api";

export interface BillOrderItem {
  menu_item_id: string;
  name: string;
  price: number;
  quantity: number;
  note?: string;
}

export interface BillOrder {
  order_id: string;
  order_number: string;
  status: string;
  total_amount: number;
  submitted_at_utc: string;
  items: BillOrderItem[];
}

export interface ManualPayment {
  id: string;
  amount: number;
  currency: string;
  payment_method: string;
  status: string;
  recorded_at_utc: string;
}

export interface ReopenEvent {
  id: string;
  reason: string;
  reopened_by: string;
  reopened_at_utc: string;
}

export interface BillSessionDetail {
  bill_session_id: string;
  table_id: string;
  status: string;
  attached_orders: BillOrder[];
  manual_payments: ManualPayment[];
  reopen_events: ReopenEvent[];
  total_amount: number;
  currency: string;
}

export interface RecordManualPaymentResponse {
  manual_payment_id: string;
  bill_session_id: string;
  amount: number;
  currency: string;
  payment_method: string;
  status: string;
  recorded_at_utc: string;
}

/**
 * Server Action to fetch active or closed bill details with attached orders,
 * payments, and reopen logs using simulated bills.view staff permission.
 */
export async function getBillDetailAction(billId: string): Promise<BillSessionDetail> {
  const response = await backendFetch(`/api/internal/bills/${billId}`, {
    method: "GET",
    permissions: "tenant.bills.view",
    next: { revalidate: 0 },
  });
  return handleApiResponse<BillSessionDetail>(response);
}

/**
 * Server Action to record an external/offline manual payment (cash, card_external_pos etc.)
 * with simulated manual_payments.record staff permission.
 */
export async function recordManualPaymentAction(
  billId: string,
  amount: number,
  paymentMethod: string,
  externalReference?: string,
  note?: string
): Promise<RecordManualPaymentResponse> {
  const response = await backendFetch(`/api/internal/bills/${billId}/manual-payments`, {
    method: "POST",
    permissions: "tenant.manual_payments.record",
    body: JSON.stringify({
      amount,
      currency: "TRY",
      payment_method: paymentMethod,
      external_reference: externalReference,
      note,
    }),
  });
  return handleApiResponse<RecordManualPaymentResponse>(response);
}

/**
 * Server Action to close a bill session, recalculating totals server-side.
 * With bills.close staff permission.
 */
export async function closeBillAction(
  billId: string,
  manualPaymentPayload?: {
    amount: number;
    payment_method: string;
    external_reference?: string;
    note?: string;
  },
  reason?: string
): Promise<BillSessionDetail> {
  const payload: Record<string, any> = { reason };
  if (manualPaymentPayload) {
    payload.manual_payment = {
      ...manualPaymentPayload,
      currency: "TRY",
    };
  }

  const response = await backendFetch(`/api/internal/bills/${billId}/close`, {
    method: "POST",
    permissions: "tenant.bills.close,tenant.manual_payments.record",
    body: JSON.stringify(payload),
  });
  return handleApiResponse<BillSessionDetail>(response);
}

/**
 * Server Action to reopen a closed bill session logging authorization reasons.
 * With bills.reopen staff permission.
 */
export async function reopenBillAction(billId: string, reason: string): Promise<BillSessionDetail> {
  const response = await backendFetch(`/api/internal/bills/${billId}/reopen`, {
    method: "POST",
    permissions: "tenant.bills.reopen",
    body: JSON.stringify({ reason }),
  });
  return handleApiResponse<BillSessionDetail>(response);
}

export interface TableStatus {
  id: string;
  name: string;
  capacity: number;
  status: string;
  bill: number;
  bill_session_id?: string;
}

export interface KitchenOrderItem {
  name: string;
  quantity: number;
}

export interface KitchenOrder {
  id: string;
  table: string;
  items: KitchenOrderItem[];
  total: number;
  time: string;
  status: string;
}

/**
 * Server Action to fetch all tables and their active bill totals for the personnel grid.
 */
export async function listTablesAction(): Promise<TableStatus[]> {
  const response = await backendFetch("/api/internal/tables", {
    method: "GET",
    permissions: "tenant.bills.view",
    next: { revalidate: 0 },
  });
  return handleApiResponse<TableStatus[]>(response);
}

/**
 * Server Action to fetch active orders for the kitchen screen.
 */
export async function listActiveOrdersAction(): Promise<KitchenOrder[]> {
  const response = await backendFetch("/api/internal/orders", {
    method: "GET",
    permissions: "tenant.bills.view",
    next: { revalidate: 0 },
  });
  return handleApiResponse<KitchenOrder[]>(response);
}

/**
 * Server Action to update the status of an order in the kitchen.
 */
export async function updateOrderStatusAction(orderId: string, status: string): Promise<KitchenOrder> {
  const response = await backendFetch(`/api/internal/orders/${orderId}/status`, {
    method: "POST",
    permissions: "tenant.bills.view",
    body: JSON.stringify({ status }),
  });
  return handleApiResponse<KitchenOrder>(response);
}
