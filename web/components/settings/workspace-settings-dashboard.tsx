"use client";

import { useCallback, useEffect, useState } from "react";
import {
  exportWorkspaceData,
  getWorkspaceSettings,
  requestWorkspaceDeletion,
  type WorkspaceSettings,
} from "../../lib/workspace-settings-api";
import { DashboardShell } from "../layout/dashboard-shell";
import { Button } from "../ui/button";
import { EmptyState } from "../ui/empty-state";
import { ErrorState } from "../ui/error-state";
import { LoadingState } from "../ui/loading-state";
import { PageHeader } from "../ui/page-header";
import { StatCard } from "../ui/stat-card";
import { StatusBadge } from "../ui/status-badge";

type WorkspaceSettingsDashboardProps = {
  workspaceId: string;
};

export function WorkspaceSettingsDashboard({
  workspaceId,
}: WorkspaceSettingsDashboardProps) {
  const [settings, setSettings] = useState<WorkspaceSettings | null>(null);
  const [reason, setReason] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [isExporting, setIsExporting] = useState(false);
  const [isRequestingDeletion, setIsRequestingDeletion] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    setIsLoading(true);
    setErrorMessage(null);

    try {
      const response = await getWorkspaceSettings(workspaceId);
      setSettings(response);
    } catch (error) {
      setErrorMessage(
        error instanceof Error
          ? error.message
          : "Could not load workspace settings.",
      );
    } finally {
      setIsLoading(false);
    }
  }, [workspaceId]);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    void refresh();
  }, [refresh]);

  async function handleExport() {
    setIsExporting(true);
    setErrorMessage(null);
    setSuccessMessage(null);

    try {
      const payload = await exportWorkspaceData(workspaceId);
      downloadJson(payload, `workspace-${workspaceId}-export.json`);
      setSuccessMessage("Workspace data export generated.");
      await refresh();
    } catch (error) {
      setErrorMessage(
        error instanceof Error
          ? error.message
          : "Could not export workspace data.",
      );
    } finally {
      setIsExporting(false);
    }
  }

  async function handleDeleteRequest() {
    const confirmed = window.confirm(
      "Request workspace deletion? Normal workspace usage will be disabled while deletion is pending.",
    );

    if (!confirmed) {
      return;
    }

    setIsRequestingDeletion(true);
    setErrorMessage(null);
    setSuccessMessage(null);

    try {
      await requestWorkspaceDeletion(workspaceId, reason);
      setReason("");
      setSuccessMessage("Workspace deletion request recorded.");
      await refresh();
    } catch (error) {
      setErrorMessage(
        error instanceof Error
          ? error.message
          : "Could not request workspace deletion.",
      );
    } finally {
      setIsRequestingDeletion(false);
    }
  }

  return (
    <DashboardShell
      activeItem="settings"
      title="Workspace settings"
      description="Manage data export and workspace lifecycle controls."
      workspaceId={workspaceId}
    >
      <PageHeader
        kicker="Settings"
        title="Data controls and lifecycle"
        description="Export workspace-owned data, review retention notes, and request soft deletion when a workspace is no longer needed."
        meta={
          <p className="font-mono text-xs text-muted-foreground">{workspaceId}</p>
        }
      />

      {errorMessage && (
        <div className="mb-6">
          <ErrorState message={errorMessage} />
        </div>
      )}

      {successMessage && (
        <div className="mb-6 rounded-2xl bg-emerald-50 px-4 py-3 text-sm font-medium text-emerald-700 ring-1 ring-emerald-200">
          {successMessage}
        </div>
      )}

      {isLoading ? (
        <LoadingState title="Loading workspace settings" />
      ) : settings ? (
        <div className="space-y-6">
          <section className="grid grid-flow-dense gap-4 md:grid-cols-3">
            <StatCard
              label="Workspace"
              value={settings.name}
              detail="Manage permission required"
            />
            <StatCard
              label="Lifecycle status"
              value={settings.status}
              detail="Normal usage requires active status"
              tone={settings.status === "active" ? "good" : "warning"}
            />
            <StatCard
              label="Current plan"
              value={settings.plan?.display_name ?? "-"}
              detail={settings.plan?.status ?? "No subscription"}
            />
          </section>

          <section className="rounded-3xl bg-card p-6 shadow-sm ring-1 ring-border/70">
            <div className="flex flex-wrap items-start justify-between gap-4">
              <div>
                <p className="text-sm font-medium text-muted-foreground">
                  Compliance and data controls
                </p>
                <h2 className="mt-1 text-2xl font-semibold tracking-tight text-card-foreground">
                  Workspace-owned export
                </h2>
                <p className="mt-2 max-w-2xl text-sm leading-6 text-muted-foreground">
                  This JSON export includes workspace-owned records, including
                  document chunks and conversation messages. Admin/support
                  metadata views remain content-restricted.
                </p>
              </div>
              <Button disabled={isExporting} onClick={() => void handleExport()}>
                {isExporting ? "Exporting" : "Export workspace data"}
              </Button>
            </div>
          </section>

          <section className="rounded-3xl bg-card p-6 shadow-sm ring-1 ring-border/70">
            <p className="text-sm font-medium text-muted-foreground">
              Retention notes
            </p>
            <div className="mt-4 grid gap-3">
              {settings.retention_notes.map((note) => (
                <div
                  key={note}
                  className="rounded-2xl bg-muted px-4 py-3 text-sm text-muted-foreground"
                >
                  {note}
                </div>
              ))}
            </div>
          </section>

          <section className="rounded-3xl bg-card p-6 shadow-sm ring-1 ring-destructive/25">
            <div className="flex flex-wrap items-start justify-between gap-4">
              <div>
                <p className="text-sm font-medium text-destructive">
                  Danger zone
                </p>
                <h2 className="mt-1 text-2xl font-semibold tracking-tight text-card-foreground">
                  Request workspace deletion
                </h2>
                <p className="mt-2 max-w-2xl text-sm leading-6 text-muted-foreground">
                  This is a soft-delete request. It disables normal workspace
                  usage while preserving rows for future retention and deletion
                  workflows.
                </p>
              </div>
              <StatusBadge status={settings.status} />
            </div>

            <textarea
              value={reason}
              onChange={(event) => setReason(event.target.value)}
              placeholder="Optional reason for the deletion request"
              className="mt-5 min-h-28 w-full rounded-2xl border border-input bg-background px-4 py-3 text-sm outline-none transition focus:ring-2 focus:ring-ring"
            />

            <div className="mt-4 flex flex-wrap gap-2">
              <Button
                variant="danger"
                disabled={
                  isRequestingDeletion || settings.status !== "active"
                }
                onClick={() => void handleDeleteRequest()}
              >
                {isRequestingDeletion
                  ? "Requesting"
                  : "Request workspace deletion"}
              </Button>
              <Button variant="secondary" onClick={() => void refresh()}>
                Refresh status
              </Button>
            </div>
          </section>
        </div>
      ) : (
        <EmptyState
          title="Settings unavailable"
          description="Workspace settings could not be loaded for this account."
        />
      )}
    </DashboardShell>
  );
}

function downloadJson(payload: unknown, filename: string) {
  const blob = new Blob([JSON.stringify(payload, null, 2)], {
    type: "application/json",
  });
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement("a");

  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.URL.revokeObjectURL(url);
}
