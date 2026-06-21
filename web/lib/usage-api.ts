import { apiRequest } from "./api";

export type UsageMetric = {
  metric_name: string;
  current: number;
  limit: number | null;
  unit: string;
};

export type UsageSummary = {
  workspace_id: string;
  metrics: UsageMetric[];
};

export async function getWorkspaceUsage(
  workspaceId: string,
): Promise<UsageSummary> {
  return apiRequest<UsageSummary>(`/workspaces/${workspaceId}/usage`);
}
