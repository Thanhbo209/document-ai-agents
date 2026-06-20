import { API_BASE_URL, apiRequest } from "./api";

export type ReviewItem = {
  id: string;
  workspace_id: string;
  target_type: string;
  target_id: string;
  field_name: string | null;
  original_value: Record<string, unknown> | null;
  reviewed_value: Record<string, unknown> | null;
  evidence: Record<string, unknown>;
  status: string;
  reviewer_user_id: string | null;
  reviewed_at: string | null;
  comments: string | null;
  created_at: string;
  updated_at: string;
};

export type CreateReviewItemInput = {
  target_type: string;
  target_id: string;
  field_name?: string;
  original_value?: Record<string, unknown>;
  evidence: Record<string, unknown>;
  actor_user_id?: string;
};

export type ReviewDecisionInput = {
  reviewer_user_id?: string;
  reviewed_value?: Record<string, unknown>;
  comments?: string;
};

export async function listReviewItems(
  workspaceId: string,
  status?: string,
): Promise<ReviewItem[]> {
  const params = new URLSearchParams();

  if (status) {
    params.set("status", status);
  }

  const query = params.toString();

  return apiRequest<ReviewItem[]>(
    `/workspaces/${workspaceId}/review-items${query ? `?${query}` : ""}`,
  );
}

export async function approveReviewItem(
  workspaceId: string,
  reviewItemId: string,
  input: ReviewDecisionInput,
): Promise<ReviewItem> {
  return apiRequest<ReviewItem>(
    `/workspaces/${workspaceId}/review-items/${reviewItemId}/approve`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(input),
    },
  );
}

export async function rejectReviewItem(
  workspaceId: string,
  reviewItemId: string,
  input: ReviewDecisionInput,
): Promise<ReviewItem> {
  return apiRequest<ReviewItem>(
    `/workspaces/${workspaceId}/review-items/${reviewItemId}/reject`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(input),
    },
  );
}

export function reviewExportUrl(
  workspaceId: string,
  format: "json" | "csv",
  status?: string,
): string {
  const params = new URLSearchParams();
  params.set("format", format);

  if (status) {
    params.set("status", status);
  }

  return `${API_BASE_URL}/workspaces/${workspaceId}/exports/review-items?${params.toString()}`;
}
