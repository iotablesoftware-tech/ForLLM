import { headers, cookies } from "next/headers";

const BACKEND_API_URL = process.env.BACKEND_API_URL || "http://localhost:8000";

export interface FetchOptions extends RequestInit {
  permissions?: string;
}

/**
 * Resolves the tenant slug dynamically from the host header on the server side.
 * e.g., demo.iotables.net -> demo
 */
export async function getTenantSlug(): Promise<string> {
  const headersList = await headers();
  const host = headersList.get("host") || "";
  const hostClean = host.split(":")[0];
  const parts = hostClean.split(".");
  
  if (parts.length >= 3 && parts[parts.length - 2] === "iotables" && parts[parts.length - 1] === "net") {
    const subdomain = parts[0];
    if (subdomain !== "platform") {
      return subdomain;
    }
  }
  
  // Fallback default tenant for local development/testing
  return "bistro-ankara";
}

/**
 * Stateless Server-to-Server API Fetch wrapper.
 * Appends dynamic tenant headers, correlation IDs, and forwards customer session cookies automatically.
 */
export async function backendFetch(path: string, options: FetchOptions = {}): Promise<Response> {
  const tenantSlug = await getTenantSlug();
  const headersList = await headers();
  
  // Setup standard headers
  const reqHeaders = new Headers(options.headers || {});
  reqHeaders.set("Content-Type", "application/json");
  reqHeaders.set("X-Tenant-Slug", tenantSlug);
  
  // Inject Correlation ID
  const correlationId = headersList.get("X-Correlation-ID") || crypto.randomUUID();
  reqHeaders.set("X-Correlation-ID", correlationId);
  
  // For internal/staff endpoints, append permissions header if provided
  if (options.permissions) {
    reqHeaders.set("X-Staff-Permissions", options.permissions);
  }
  
  // Forward customer session cookies if present
  const cookieStore = await cookies();
  const customerSession = cookieStore.get("customer_session");
  if (customerSession) {
    reqHeaders.set("Cookie", `customer_session=${customerSession.value}`);
  }
  
  const cleanPath = path.startsWith("/") ? path : `/${path}`;
  const url = `${BACKEND_API_URL}${cleanPath}`;
  
  return fetch(url, {
    ...options,
    headers: reqHeaders,
  });
}

/**
 * Convenience helper to handle JSON response parsing and common RFC 7807 error details.
 */
export async function handleApiResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    let errorDetail = "Backend API request failed.";
    try {
      const errorJson = await response.json();
      errorDetail = errorJson.detail || errorJson.title || errorDetail;
    } catch {
      // Fallback
    }
    throw new Error(errorDetail);
  }
  
  return response.json() as Promise<T>;
}
