"use client";

import { useCallback, useEffect, useState } from "react";
import { DashboardShell } from "../layout/dashboard-shell";
import { ErrorState } from "../ui/error-state";
import { LoadingState } from "../ui/loading-state";
import { listDocuments, WorkspaceDocument } from "../../lib/upload-api";
import { getWorkspaceUsage, UsageMetric, UsagePlan } from "../../lib/usage-api";
import { getWorkspaceSettings, WorkspaceSettings } from "../../lib/workspace-settings-api";
import { OverviewHero } from "../dashboard/overview/overview-hero";
import { WorkspaceKpiGrid } from "../dashboard/overview/workspace-kpi-grid";
import { UsageOverviewChart } from "../dashboard/overview/usage-overview-chart";
import { RecentActivityCard } from "../dashboard/overview/recent-activity-card";
import { QuickActionsCard } from "../dashboard/overview/quick-actions-card";

type WorkspaceUploadManagerProps = {
  workspaceId: string;
};

/**
 * WorkspaceUploadManager has been refactored into the workspace Overview dashboard.
 * The document library now lives at /documents/[workspaceId].
 */
export function WorkspaceUploadManager({
  workspaceId,
}: WorkspaceUploadManagerProps) {
  const [documents, setDocuments] = useState<WorkspaceDocument[]>([]);
  const [metrics, setMetrics] = useState<UsageMetric[]>([]);
  const [plan, setPlan] = useState<UsagePlan | null>(null);
  const [settings, setSettings] = useState<WorkspaceSettings | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    setIsLoading(true);
    setErrorMessage(null);

    try {
      const [docsResponse, usageResponse, settingsResponse] = await Promise.all([
        listDocuments(workspaceId),
        getWorkspaceUsage(workspaceId),
        getWorkspaceSettings(workspaceId).catch(() => null),
      ]);

      setDocuments(docsResponse.documents);
      setMetrics(usageResponse.metrics);
      setPlan(usageResponse.plan);
      setSettings(settingsResponse);
    } catch (error) {
      setErrorMessage(
        error instanceof Error ? error.message : "Could not load workspace data.",
      );
    } finally {
      setIsLoading(false);
    }
  }, [workspaceId]);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    void refresh();
  }, [refresh]);

  const workspaceName = settings?.name ?? "Your workspace";
  const workspaceStatus = settings?.status ?? "active";
  const planDisplayName = plan?.display_name ?? settings?.plan?.display_name ?? "Free";

  return (
    <DashboardShell
      activeItem="overview"
      title="Overview"
      description="Workspace health, usage, and activity at a glance."
      workspaceId={workspaceId}
    >
      {isLoading ? (
        <LoadingState title="Loading workspace" rows={4} />
      ) : errorMessage ? (
        <ErrorState message={errorMessage} />
      ) : (
        <div className="grid gap-6">
          {/* Hero */}
          <OverviewHero
            workspaceName={workspaceName}
            workspaceStatus={workspaceStatus}
            planName={planDisplayName}
          />

          {/* KPI cards */}
          <WorkspaceKpiGrid
            documents={documents}
            metrics={metrics}
            planDisplayName={planDisplayName}
          />

          {/* Usage overview */}
          {metrics.length > 0 && (
            <UsageOverviewChart metrics={metrics} />
          )}

          {/* Recent activity + Quick actions */}
          <div className="grid gap-6 lg:grid-cols-2">
            <RecentActivityCard
              documents={documents}
              workspaceId={workspaceId}
            />
            <QuickActionsCard workspaceId={workspaceId} />
          </div>
        </div>
      )}
    </DashboardShell>
  );
}
