import { apiRequest } from "./api";

export type UsageMetric = {
  metric_name: string;
  current: number;
  limit: number | null;
  unit: string;
};

export type UsagePlan = {
  name: string;
  display_name: string;
  status: string;
};

export type UsageSummary = {
  workspace_id: string;
  plan: UsagePlan;
  metrics: UsageMetric[];
};

export async function getWorkspaceUsage(
  workspaceId: string,
): Promise<UsageSummary> {
  return apiRequest<UsageSummary>(`/workspaces/${workspaceId}/usage`);
}
