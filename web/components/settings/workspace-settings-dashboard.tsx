"use client";

import { useCallback, useEffect, useState } from "react";
import {
  exportWorkspaceData,
  getWorkspaceSettings,
  requestWorkspaceDeletion,
  type WorkspaceSettings,
} from "../../lib/workspace-settings-api";
import { DashboardShell } from "../layout/dashboard-shell";
import { ErrorState } from "../ui/error-state";
import { LoadingState } from "../ui/loading-state";
import { PageHeader } from "../ui/page-header";
import { EmptyState } from "../ui/empty-state";
import { WorkspaceOverviewCard } from "./workspace-overview-card";
import { DataExportCard } from "./data-export-card";
import { DangerZoneCard } from "./danger-zone-card";
import { ComplianceNoteCard } from "./compliance-note-card";

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
      downloadJson(
        payload,
        `workspace-export-${new Date().toISOString().split("T")[0]}.json`,
      );
      setSuccessMessage("Workspace data export downloaded.");
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
    setIsRequestingDeletion(true);
    setErrorMessage(null);
    setSuccessMessage(null);

    try {
      await requestWorkspaceDeletion(workspaceId, reason);
      setReason("");
      setSuccessMessage(
        "Workspace removal request recorded. Normal operations will be disabled.",
      );
      await refresh();
    } catch (error) {
      setErrorMessage(
        error instanceof Error
          ? error.message
          : "Could not submit the removal request.",
      );
    } finally {
      setIsRequestingDeletion(false);
    }
  }

  return (
    <DashboardShell
      activeItem="settings"
      title="Settings"
      description="Manage workspace data controls and lifecycle."
      workspaceId={workspaceId}
    >
      <PageHeader
        kicker="Settings"
        title="Data controls and lifecycle"
        description="Export your workspace data, review compliance notes, and manage the workspace lifecycle."
      />

      {errorMessage && (
        <div className="mb-6">
          <ErrorState message={errorMessage} />
        </div>
      )}

      {successMessage && (
        <div className="mb-6 rounded-2xl bg-emerald-50 px-4 py-3 text-sm font-medium text-emerald-700 ring-1 ring-emerald-200 dark:bg-emerald-950/30 dark:text-emerald-400 dark:ring-emerald-800">
          {successMessage}
        </div>
      )}

      {isLoading ? (
        <LoadingState title="Loading settings" rows={3} />
      ) : settings ? (
        <div className="space-y-6">
          {/* Workspace info — masked ID, no raw UUID */}
          <WorkspaceOverviewCard settings={settings} />

          {/* Retention notes */}
          {settings.retention_notes.length > 0 && (
            <section className="rounded-3xl bg-card p-6 shadow-sm ring-1 ring-border/70">
              <p className="text-sm font-medium text-muted-foreground">
                Data retention
              </p>
              <h3 className="mt-1 text-xl font-semibold tracking-tight text-card-foreground">
                Retention notes
              </h3>
              <ul className="mt-4 space-y-2">
                {settings.retention_notes.map((note) => (
                  <li
                    key={note}
                    className="flex items-start gap-2.5 rounded-2xl bg-muted px-4 py-3 text-sm text-muted-foreground"
                  >
                    <svg
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="2"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      className="mt-0.5 h-4 w-4 shrink-0"
                      aria-hidden="true"
                    >
                      <path d="M9 12h6M12 9v6" />
                      <circle cx="12" cy="12" r="9" />
                    </svg>
                    {note}
                  </li>
                ))}
              </ul>
            </section>
          )}

          {/* Compliance note */}
          <ComplianceNoteCard />

          {/* Data export */}
          <DataExportCard
            isExporting={isExporting}
            onExport={() => void handleExport()}
          />

          {/* Danger zone — inline confirmation, no window.confirm */}
          <DangerZoneCard
            workspaceStatus={settings.status}
            isRequestingDeletion={isRequestingDeletion}
            reason={reason}
            onReasonChange={setReason}
            onConfirmDelete={() => void handleDeleteRequest()}
          />
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
