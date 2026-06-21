import { getAccessToken } from "./auth-token";

export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000/api/v1";

export async function apiRequest<T>(
  path: string,
  init?: RequestInit,
): Promise<T> {
  const token = getAccessToken();
  const headers = new Headers(init?.headers);

  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers,
    cache: "no-store",
  });

  if (!response.ok) {
    const errorBody = await safeReadJson(response);
    throw new Error(formatApiError(response.status, errorBody));
  }

  return response.json() as Promise<T>;
}

export async function safeReadJson(response: Response): Promise<unknown> {
  try {
    return await response.json();
  } catch {
    return null;
  }
}

export function formatApiError(status: number, body: unknown): string {
  if (status === 401) {
    return "Please log in again.";
  }

  if (status === 410) {
    return "This workspace is no longer active.";
  }

  if (body && typeof body === "object" && "detail" in body) {
    const detail = (body as { detail: unknown }).detail;

    if (typeof detail === "string") {
      if (status === 403) {
        if (detail.includes("pending deletion")) {
          return "This workspace is no longer active.";
        }

        return "You do not have permission to access this workspace.";
      }

      return detail;
    }

    if (status === 429) {
      return formatQuotaError(detail);
    }

    if (status === 422) {
      return formatValidationError(detail);
    }

    return JSON.stringify(detail);
  }

  if (status === 403) {
    return "You do not have permission to access this workspace.";
  }

  return `Request failed with status ${status}.`;
}

function formatQuotaError(detail: unknown): string {
  if (detail && typeof detail === "object") {
    const payload = detail as {
      metric_name?: unknown;
      current?: unknown;
      attempted?: unknown;
      limit?: unknown;
      message?: unknown;
    };

    if (
      typeof payload.metric_name === "string" &&
      typeof payload.current === "number" &&
      typeof payload.attempted === "number" &&
      typeof payload.limit === "number"
    ) {
      return `Quota exceeded for ${payload.metric_name}: ${payload.current + payload.attempted}/${payload.limit}.`;
    }

    if (typeof payload.message === "string") {
      return payload.message;
    }
  }

  return "Workspace quota exceeded.";
}

function formatValidationError(detail: unknown): string {
  if (detail && typeof detail === "object" && "message" in detail) {
    const message = (detail as { message: unknown }).message;

    if (typeof message === "string") {
      return message;
    }
  }

  return JSON.stringify(detail);
}
