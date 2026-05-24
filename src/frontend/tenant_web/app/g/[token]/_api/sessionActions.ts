"use server";

import { cookies } from "next/headers";
import { backendFetch, handleApiResponse } from "../../../../lib/api";

interface SessionResponse {
  id: string;
  table_id: string;
  status: string;
  expires_at_utc: string;
  extension_count: number;
}

/**
 * Server Action to validate the QR token, register a fresh guest session,
 * and save the customer_session cookie dynamically on the client.
 */
export async function joinSessionAction(qrToken: string): Promise<SessionResponse> {
  const response = await backendFetch("/api/sessions/join", {
    method: "POST",
    body: JSON.stringify({ qr_token: qrToken }),
  });

  if (!response.ok) {
    let errMsg = "QR kod doğrulanamadı.";
    try {
      const errData = await response.json();
      errMsg = errData.detail || errMsg;
    } catch {
      // Fallback
    }
    throw new Error(errMsg);
  }

  const data: SessionResponse = await response.json();

  // Forward the session cookie returned by the backend or set it locally
  const cookieStore = await cookies();
  cookieStore.set({
    name: "customer_session",
    value: data.id,
    httpOnly: true,
    secure: process.env.NODE_ENV === "production",
    sameSite: "strict",
    path: "/",
    maxAge: 600, // 10 minutes
  });

  return data;
}

/**
 * Server Action to extend the current active guest session.
 */
export async function extendSessionAction(sessionId: string): Promise<SessionResponse> {
  const response = await backendFetch("/api/sessions/extend", {
    method: "POST",
    body: JSON.stringify({ session_id: sessionId }),
  });

  const data = await handleApiResponse<SessionResponse>(response);

  // Extend cookie expiration locally
  const cookieStore = await cookies();
  cookieStore.set({
    name: "customer_session",
    value: data.id,
    httpOnly: true,
    secure: process.env.NODE_ENV === "production",
    sameSite: "strict",
    path: "/",
    maxAge: 600, // 10 minutes extension
  });

  return data;
}

export interface MenuItem {
  id: string;
  name: string;
  price: number;
  category: string;
  status: string;
}

/**
 * Server Action to fetch the dynamic guest menu catalog.
 */
export async function getMenuAction(): Promise<MenuItem[]> {
  const response = await backendFetch("/api/sessions/menu", {
    method: "GET",
    next: { revalidate: 300 }, // Cache for 5 minutes
  });
  return handleApiResponse<MenuItem[]>(response);
}
