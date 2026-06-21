import {
  API_BASE_URL,
  apiRequest,
  formatApiError,
  safeReadJson,
} from "./api-client";
import { getAccessToken } from "./auth-token";

export {
  API_BASE_URL,
  apiRequest,
  formatApiError,
  safeReadJson,
} from "./api-client";
export {
  exportWorkspaceData,
  getWorkspaceSettings,
  markWorkspaceDeleted,
  requestWorkspaceDeletion,
} from "./workspace-settings-api";
export type {
  WorkspaceComplianceExport,
  WorkspaceSettings,
  WorkspaceStatus,
} from "./workspace-settings-api";

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

export type AdminWorkspaceSummary = {
  id: string;
  name: string;
  owner_user_id: string;
  owner_email: string;
  status: string;
  document_count: number;
  failed_job_count: number;
  storage_bytes: number;
  plan_name: string;
  created_at: string;
};

export type AdminJobSummary = {
  id: string;
  workspace_id: string;
  document_id: string;
  status: string;
  error_message: string | null;
  created_at: string;
  updated_at: string;
};

export type AdminAuditEvent = {
  id: string;
  workspace_id: string;
  actor_user_id: string | null;
  event_type: string;
  entity_type: string;
  entity_id: string | null;
  payload: Record<string, unknown>;
  created_at: string;
};

export type AdminDocumentMetadata = {
  id: string;
  workspace_id: string;
  title: string;
  source_type: string;
  status: string;
  created_at: string;
  updated_at: string;
  file_count: number;
  chunk_count: number;
};

type AdminJobFilters = {
  workspace_id?: string;
  status?: string;
};

type AdminAuditFilters = {
  workspace_id?: string;
  event_type?: string;
  actor_user_id?: string;
};

export async function listAdminWorkspaces(): Promise<AdminWorkspaceSummary[]> {
  return apiRequest<AdminWorkspaceSummary[]>("/admin/workspaces");
}

export async function listAdminJobs(
  params?: AdminJobFilters,
): Promise<AdminJobSummary[]> {
  return apiRequest<AdminJobSummary[]>(withQuery("/admin/jobs", params));
}

export async function listAdminWorkspaceDocuments(
  workspaceId: string,
): Promise<AdminDocumentMetadata[]> {
  return apiRequest<AdminDocumentMetadata[]>(
    `/admin/workspaces/${workspaceId}/documents`,
  );
}

export async function searchAdminAuditEvents(
  params?: AdminAuditFilters,
): Promise<AdminAuditEvent[]> {
  return apiRequest<AdminAuditEvent[]>(
    withQuery("/admin/audit-events", params),
  );
}

export async function downloadAdminAuditExport(
  format: "csv" | "json",
  params?: AdminAuditFilters,
): Promise<void> {
  const token = getAccessToken();
  const headers = new Headers();

  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  const response = await fetch(
    `${API_BASE_URL}${withQuery("/admin/audit-events/export", {
      format,
      ...params,
    })}`,
    {
      headers,
      cache: "no-store",
    },
  );

  if (!response.ok) {
    const errorBody = await safeReadJson(response);
    throw new Error(formatApiError(response.status, errorBody));
  }

  const blob = await response.blob();
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement("a");

  link.href = url;
  link.download = `audit-events.${format}`;
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.URL.revokeObjectURL(url);
}

function withQuery(
  path: string,
  params?: Record<string, string | undefined>,
): string {
  const query = new URLSearchParams();

  for (const [key, value] of Object.entries(params ?? {})) {
    if (value) {
      query.set(key, value);
    }
  }

  const queryString = query.toString();
  return queryString ? `${path}?${queryString}` : path;
}
