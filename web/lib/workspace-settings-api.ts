import { apiRequest } from "./api-client";

export type WorkspaceStatus = {
  workspace_id: string;
  status: string;
  deletion_requested_at: string | null;
  deleted_at: string | null;
};

export type WorkspaceSettings = {
  workspace_id: string;
  name: string;
  status: string;
  deletion_requested_at: string | null;
  deleted_at: string | null;
  plan: {
    name: string;
    display_name: string;
    status: string;
  } | null;
  retention_notes: string[];
};

export type WorkspaceComplianceExport = Record<string, unknown>;

export async function getWorkspaceSettings(
  workspaceId: string,
): Promise<WorkspaceSettings> {
  return apiRequest<WorkspaceSettings>(`/workspaces/${workspaceId}/settings`);
}

export async function exportWorkspaceData(
  workspaceId: string,
): Promise<WorkspaceComplianceExport> {
  return apiRequest<WorkspaceComplianceExport>(
    `/workspaces/${workspaceId}/compliance/export`,
  );
}

export async function requestWorkspaceDeletion(
  workspaceId: string,
  reason: string,
): Promise<WorkspaceStatus> {
  return apiRequest<WorkspaceStatus>(
    `/workspaces/${workspaceId}/compliance/delete-request`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ reason: reason || null }),
    },
  );
}

export async function markWorkspaceDeleted(
  workspaceId: string,
): Promise<WorkspaceStatus> {
  return apiRequest<WorkspaceStatus>(
    `/workspaces/${workspaceId}/compliance/mark-deleted`,
    {
      method: "POST",
    },
  );
}
