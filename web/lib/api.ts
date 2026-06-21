import { getAccessToken } from "./auth-api";

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
  if (body && typeof body === "object" && "detail" in body) {
    const detail = (body as { detail: unknown }).detail;

    if (typeof detail === "string") {
      return detail;
    }

    return JSON.stringify(detail);
  }

  return `Request failed with status ${status}.`;
}

export type PlanLimits = {
  storage_bytes_limit: number;
  documents_limit: number;
  daily_query_limit: number;
  monthly_embedding_token_limit: number;
  monthly_llm_token_limit: number;
  concurrent_job_limit: number;
};

export type BillingPlan = {
  name: string;
  display_name: string;
  description: string;
  limits: PlanLimits;
};

export type BillingSubscription = {
  id: string;
  workspace_id: string;
  plan_name: string;
  status: string;
  current_period_start: string | null;
  current_period_end: string | null;
};

export type BillingSummary = {
  workspace_id: string;
  subscription: BillingSubscription;
  plan: BillingPlan;
};

export type ChangePlanInput = {
  plan_name: string;
};

export async function getBillingSummary(
  workspaceId: string,
): Promise<BillingSummary> {
  return apiRequest<BillingSummary>(`/workspaces/${workspaceId}/billing`);
}

export async function listBillingPlans(
  workspaceId: string,
): Promise<BillingPlan[]> {
  return apiRequest<BillingPlan[]>(`/workspaces/${workspaceId}/billing/plans`);
}

export async function changeWorkspacePlan(
  workspaceId: string,
  planName: string,
): Promise<BillingSummary> {
  const input: ChangePlanInput = {
    plan_name: planName,
  };

  return apiRequest<BillingSummary>(`/workspaces/${workspaceId}/billing/plan`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(input),
  });
}
