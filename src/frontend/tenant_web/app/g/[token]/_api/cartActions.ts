"use server";

import { cookies } from "next/headers";
import { backendFetch, handleApiResponse } from "../../../../lib/api";

export interface CartItem {
  menu_item_id: string;
  name: string;
  price: number;
  quantity: number;
  note?: string;
  station_code: string;
}

export interface Cart {
  cart_version: number;
  total_amount: number;
  items: Record<string, CartItem>;
}

export interface SubmitOrderResponse {
  order_id: string;
  order_number: string;
  status: string;
  submitted_at_utc: string;
  total_amount: number;
  currency: string;
  station_ticket_count: number;
  session_status: string;
}

/**
 * Server Action to fetch the current collaborative cart from Redis.
 */
export async function getCartAction(): Promise<Cart> {
  const response = await backendFetch("/api/cart", {
    method: "GET",
    next: { revalidate: 0 }, // Disable next.js cache for dynamic live data
  });
  return handleApiResponse<Cart>(response);
}

/**
 * Server Action to add an item to the collaborative cart.
 */
export async function addCartItemAction(
  menuItemId: string,
  quantity: number,
  expectedVersion: number,
  note?: string
): Promise<Cart> {
  const response = await backendFetch("/api/cart/items", {
    method: "POST",
    body: JSON.stringify({
      menu_item_id: menuItemId,
      quantity,
      expected_version: expectedVersion,
      note,
    }),
  });
  return handleApiResponse<Cart>(response);
}

/**
 * Server Action to update quantity/note of an existing item in the cart.
 */
export async function updateCartItemAction(
  menuItemId: string,
  quantity: number,
  expectedVersion: number,
  note?: string
): Promise<Cart> {
  const response = await backendFetch(`/api/cart/items/${menuItemId}`, {
    method: "PATCH",
    body: JSON.stringify({
      quantity,
      expected_version: expectedVersion,
      note,
    }),
  });
  return handleApiResponse<Cart>(response);
}

/**
 * Server Action to remove an item from the collaborative cart.
 */
export async function deleteCartItemAction(
  menuItemId: string,
  expectedVersion: number
): Promise<Cart> {
  const response = await backendFetch(`/api/cart/items/${menuItemId}`, {
    method: "DELETE",
    body: JSON.stringify({
      expected_version: expectedVersion,
    }),
  });
  return handleApiResponse<Cart>(response);
}

/**
 * Server Action to submit the collaborative cart as a live order,
 * which automatically voids/cancels the guest session and cleans local cookies.
 */
export async function submitOrderAction(
  expectedVersion: number,
  clientNote?: string
): Promise<SubmitOrderResponse> {
  const response = await backendFetch("/api/orders/submit", {
    method: "POST",
    body: JSON.stringify({
      expected_version: expectedVersion,
      client_note: clientNote,
    }),
  });

  const data = await handleApiResponse<SubmitOrderResponse>(response);

  // Clear customer session cookies locally on order submission
  const cookieStore = await cookies();
  cookieStore.delete("customer_session");

  return data;
}
