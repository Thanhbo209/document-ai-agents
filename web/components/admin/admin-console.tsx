"use client";

import { useCallback, useEffect, useState } from "react";
import {
  AdminAuditEvent,
  AdminDocumentMetadata,
  AdminJobSummary,
  AdminWorkspaceSummary,
  downloadAdminAuditExport,
  listAdminJobs,
  listAdminWorkspaceDocuments,
  listAdminWorkspaces,
  searchAdminAuditEvents,
} from "../../lib/api";

type AdminTab = "workspaces" | "jobs" | "audit";

type JobFilters = {
  workspace_id: string;
  status: string;
};

type AuditFilters = {
  workspace_id: string;
  event_type: string;
  actor_user_id: string;
};

export function AdminConsole() {
  const [activeTab, setActiveTab] = useState<AdminTab>("workspaces");
  const [workspaces, setWorkspaces] = useState<AdminWorkspaceSummary[]>([]);
  const [jobs, setJobs] = useState<AdminJobSummary[]>([]);
  const [auditEvents, setAuditEvents] = useState<AdminAuditEvent[]>([]);
  const [documents, setDocuments] = useState<AdminDocumentMetadata[]>([]);
  const [selectedWorkspaceId, setSelectedWorkspaceId] = useState<string | null>(
    null,
  );
  const [jobFilters, setJobFilters] = useState<JobFilters>({
    workspace_id: "",
    status: "",
  });
  const [auditFilters, setAuditFilters] = useState<AuditFilters>({
    workspace_id: "",
    event_type: "",
    actor_user_id: "",
  });
  const [isLoading, setIsLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const refreshWorkspaces = useCallback(async () => {
    const workspaceResults = await listAdminWorkspaces();
    setWorkspaces(workspaceResults);
  }, []);

  const refreshJobs = useCallback(async () => {
    const jobResults = await listAdminJobs(cleanFilters(jobFilters));
    setJobs(jobResults);
  }, [jobFilters]);

  const refreshAuditEvents = useCallback(async () => {
    const auditResults = await searchAdminAuditEvents(cleanFilters(auditFilters));
    setAuditEvents(auditResults);
  }, [auditFilters]);

  const refreshAll = useCallback(async () => {
    setIsLoading(true);
    setErrorMessage(null);

    try {
      await Promise.all([
        refreshWorkspaces(),
        refreshJobs(),
        refreshAuditEvents(),
      ]);
    } catch (error) {
      setErrorMessage(
        error instanceof Error ? error.message : "Could not load admin data.",
      );
    } finally {
      setIsLoading(false);
    }
  }, [refreshAuditEvents, refreshJobs, refreshWorkspaces]);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    void refreshAll();
  }, [refreshAll]);

  async function loadDocuments(workspaceId: string) {
    setSelectedWorkspaceId(workspaceId);
    setErrorMessage(null);

    try {
      const documentResults = await listAdminWorkspaceDocuments(workspaceId);
      setDocuments(documentResults);
    } catch (error) {
      setErrorMessage(
        error instanceof Error
          ? error.message
          : "Could not load document metadata.",
      );
    }
  }

  async function exportAudit(format: "csv" | "json") {
    setErrorMessage(null);

    try {
      await downloadAdminAuditExport(format, cleanFilters(auditFilters));
    } catch (error) {
      setErrorMessage(
        error instanceof Error ? error.message : "Could not export audit events.",
      );
    }
  }

  return (
    <main className="min-h-screen bg-slate-50 px-6 py-8">
      <div className="mx-auto max-w-7xl">
        <header className="mb-8">
          <p className="text-sm font-medium text-slate-500">
            Platform admin
          </p>
          <h1 className="mt-2 text-3xl font-bold tracking-tight text-slate-950">
            Support Console
          </h1>
          <p className="mt-2 max-w-3xl text-slate-600">
            Inspect tenant metadata, failed jobs, billing plan metadata, and
            audit events. Document and chunk text are intentionally omitted.
          </p>
        </header>

        {errorMessage && (
          <p className="mb-6 rounded-lg bg-red-50 px-4 py-3 text-sm text-red-700">
            {errorMessage}
          </p>
        )}

        <div className="mb-6 flex flex-wrap gap-2">
          <TabButton
            label="Workspaces"
            isActive={activeTab === "workspaces"}
            onClick={() => setActiveTab("workspaces")}
          />
          <TabButton
            label="Jobs"
            isActive={activeTab === "jobs"}
            onClick={() => setActiveTab("jobs")}
          />
          <TabButton
            label="Audit Events"
            isActive={activeTab === "audit"}
            onClick={() => setActiveTab("audit")}
          />
          <button
            type="button"
            onClick={() => void refreshAll()}
            className="rounded-lg border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700"
          >
            Refresh
          </button>
        </div>

        {isLoading ? (
          <div className="rounded-2xl border border-slate-200 bg-white p-10 text-center text-slate-500">
            Loading admin console...
          </div>
        ) : (
          <>
            {activeTab === "workspaces" && (
              <WorkspacesSection
                workspaces={workspaces}
                selectedWorkspaceId={selectedWorkspaceId}
                documents={documents}
                onLoadDocuments={(workspaceId) => void loadDocuments(workspaceId)}
              />
            )}
            {activeTab === "jobs" && (
              <JobsSection
                jobs={jobs}
                filters={jobFilters}
                onChangeFilters={setJobFilters}
                onSearch={() => void refreshJobs()}
              />
            )}
            {activeTab === "audit" && (
              <AuditSection
                events={auditEvents}
                filters={auditFilters}
                onChangeFilters={setAuditFilters}
                onSearch={() => void refreshAuditEvents()}
                onExport={(format) => void exportAudit(format)}
              />
            )}
          </>
        )}
      </div>
    </main>
  );
}

function TabButton({
  label,
  isActive,
  onClick,
}: {
  label: string;
  isActive: boolean;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`rounded-lg px-4 py-2 text-sm font-medium ${
        isActive
          ? "bg-slate-950 text-white"
          : "border border-slate-300 bg-white text-slate-700"
      }`}
    >
      {label}
    </button>
  );
}

function WorkspacesSection({
  workspaces,
  selectedWorkspaceId,
  documents,
  onLoadDocuments,
}: {
  workspaces: AdminWorkspaceSummary[];
  selectedWorkspaceId: string | null;
  documents: AdminDocumentMetadata[];
  onLoadDocuments: (workspaceId: string) => void;
}) {
  return (
    <section className="space-y-6">
      <TableShell>
        <table className="min-w-full divide-y divide-slate-200 text-sm">
          <thead className="bg-slate-100 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">
            <tr>
              <Th>Workspace</Th>
              <Th>Owner</Th>
              <Th>Documents</Th>
              <Th>Failed jobs</Th>
              <Th>Storage</Th>
              <Th>Plan</Th>
              <Th>Created</Th>
              <Th>Metadata</Th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 bg-white">
            {workspaces.map((workspace) => (
              <tr key={workspace.id}>
                <Td>
                  <div className="font-medium text-slate-950">
                    {workspace.name}
                  </div>
                  <div className="font-mono text-xs text-slate-400">
                    {workspace.id}
                  </div>
                </Td>
                <Td>
                  <div>{workspace.owner_email}</div>
                  <div className="font-mono text-xs text-slate-400">
                    {workspace.owner_user_id}
                  </div>
                </Td>
                <Td>{workspace.document_count.toLocaleString()}</Td>
                <Td>{workspace.failed_job_count.toLocaleString()}</Td>
                <Td>{formatBytes(workspace.storage_bytes)}</Td>
                <Td>{workspace.plan_name}</Td>
                <Td>{formatDate(workspace.created_at)}</Td>
                <Td>
                  <button
                    type="button"
                    onClick={() => onLoadDocuments(workspace.id)}
                    className="rounded-lg border border-slate-300 px-3 py-1.5 text-xs font-medium text-slate-700"
                  >
                    View documents
                  </button>
                </Td>
              </tr>
            ))}
          </tbody>
        </table>
      </TableShell>

      {selectedWorkspaceId && (
        <section className="rounded-2xl border border-slate-200 bg-white p-5">
          <h2 className="text-lg font-semibold text-slate-950">
            Document metadata
          </h2>
          <p className="mt-1 font-mono text-xs text-slate-400">
            {selectedWorkspaceId}
          </p>
          <div className="mt-4 overflow-x-auto">
            <table className="min-w-full divide-y divide-slate-200 text-sm">
              <thead className="bg-slate-100 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">
                <tr>
                  <Th>Title</Th>
                  <Th>Status</Th>
                  <Th>Source</Th>
                  <Th>Files</Th>
                  <Th>Chunks</Th>
                  <Th>Updated</Th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {documents.map((document) => (
                  <tr key={document.id}>
                    <Td>
                      <div className="font-medium text-slate-950">
                        {document.title}
                      </div>
                      <div className="font-mono text-xs text-slate-400">
                        {document.id}
                      </div>
                    </Td>
                    <Td>{document.status}</Td>
                    <Td>{document.source_type}</Td>
                    <Td>{document.file_count}</Td>
                    <Td>{document.chunk_count}</Td>
                    <Td>{formatDate(document.updated_at)}</Td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      )}
    </section>
  );
}

function JobsSection({
  jobs,
  filters,
  onChangeFilters,
  onSearch,
}: {
  jobs: AdminJobSummary[];
  filters: JobFilters;
  onChangeFilters: (filters: JobFilters) => void;
  onSearch: () => void;
}) {
  return (
    <section className="space-y-4">
      <div className="grid gap-3 rounded-2xl border border-slate-200 bg-white p-5 md:grid-cols-[1fr_220px_auto]">
        <input
          value={filters.workspace_id}
          onChange={(event) =>
            onChangeFilters({ ...filters, workspace_id: event.target.value })
          }
          placeholder="Workspace ID"
          className="rounded-lg border border-slate-300 px-4 py-2 text-sm"
        />
        <select
          value={filters.status}
          onChange={(event) =>
            onChangeFilters({ ...filters, status: event.target.value })
          }
          className="rounded-lg border border-slate-300 px-4 py-2 text-sm"
        >
          <option value="">All statuses</option>
          <option value="queued">Queued</option>
          <option value="processing">Processing</option>
          <option value="succeeded">Succeeded</option>
          <option value="failed">Failed</option>
        </select>
        <button
          type="button"
          onClick={onSearch}
          className="rounded-lg bg-slate-950 px-5 py-2 text-sm font-medium text-white"
        >
          Search jobs
        </button>
      </div>

      <TableShell>
        <table className="min-w-full divide-y divide-slate-200 text-sm">
          <thead className="bg-slate-100 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">
            <tr>
              <Th>Job</Th>
              <Th>Workspace</Th>
              <Th>Document</Th>
              <Th>Status</Th>
              <Th>Error</Th>
              <Th>Updated</Th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 bg-white">
            {jobs.map((job) => (
              <tr key={job.id}>
                <Td>
                  <span className="font-mono text-xs">{job.id}</span>
                </Td>
                <Td>
                  <span className="font-mono text-xs">{job.workspace_id}</span>
                </Td>
                <Td>
                  <span className="font-mono text-xs">{job.document_id}</span>
                </Td>
                <Td>{job.status}</Td>
                <Td>{job.error_message ?? "-"}</Td>
                <Td>{formatDate(job.updated_at)}</Td>
              </tr>
            ))}
          </tbody>
        </table>
      </TableShell>
    </section>
  );
}

function AuditSection({
  events,
  filters,
  onChangeFilters,
  onSearch,
  onExport,
}: {
  events: AdminAuditEvent[];
  filters: AuditFilters;
  onChangeFilters: (filters: AuditFilters) => void;
  onSearch: () => void;
  onExport: (format: "csv" | "json") => void;
}) {
  return (
    <section className="space-y-4">
      <div className="grid gap-3 rounded-2xl border border-slate-200 bg-white p-5 md:grid-cols-4">
        <input
          value={filters.workspace_id}
          onChange={(event) =>
            onChangeFilters({ ...filters, workspace_id: event.target.value })
          }
          placeholder="Workspace ID"
          className="rounded-lg border border-slate-300 px-4 py-2 text-sm"
        />
        <input
          value={filters.event_type}
          onChange={(event) =>
            onChangeFilters({ ...filters, event_type: event.target.value })
          }
          placeholder="Event type"
          className="rounded-lg border border-slate-300 px-4 py-2 text-sm"
        />
        <input
          value={filters.actor_user_id}
          onChange={(event) =>
            onChangeFilters({ ...filters, actor_user_id: event.target.value })
          }
          placeholder="Actor user ID"
          className="rounded-lg border border-slate-300 px-4 py-2 text-sm"
        />
        <button
          type="button"
          onClick={onSearch}
          className="rounded-lg bg-slate-950 px-5 py-2 text-sm font-medium text-white"
        >
          Search events
        </button>
      </div>

      <div className="flex flex-wrap gap-2">
        <button
          type="button"
          onClick={() => onExport("csv")}
          className="rounded-lg border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-700"
        >
          Export audit CSV
        </button>
        <button
          type="button"
          onClick={() => onExport("json")}
          className="rounded-lg border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-700"
        >
          Export audit JSON
        </button>
      </div>

      <TableShell>
        <table className="min-w-full divide-y divide-slate-200 text-sm">
          <thead className="bg-slate-100 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">
            <tr>
              <Th>Event</Th>
              <Th>Workspace</Th>
              <Th>Actor</Th>
              <Th>Entity</Th>
              <Th>Created</Th>
              <Th>Payload preview</Th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 bg-white">
            {events.map((event) => (
              <tr key={event.id}>
                <Td>{event.event_type}</Td>
                <Td>
                  <span className="font-mono text-xs">{event.workspace_id}</span>
                </Td>
                <Td>
                  <span className="font-mono text-xs">
                    {event.actor_user_id ?? "-"}
                  </span>
                </Td>
                <Td>
                  <div>{event.entity_type}</div>
                  <div className="font-mono text-xs text-slate-400">
                    {event.entity_id ?? "-"}
                  </div>
                </Td>
                <Td>{formatDate(event.created_at)}</Td>
                <Td>
                  <code className="block max-w-md truncate rounded bg-slate-100 px-2 py-1 text-xs text-slate-700">
                    {payloadPreview(event.payload)}
                  </code>
                </Td>
              </tr>
            ))}
          </tbody>
        </table>
      </TableShell>
    </section>
  );
}

function TableShell({ children }: { children: React.ReactNode }) {
  return (
    <div className="overflow-x-auto rounded-2xl border border-slate-200 bg-white shadow-sm">
      {children}
    </div>
  );
}

function Th({ children }: { children: React.ReactNode }) {
  return <th className="px-4 py-3">{children}</th>;
}

function Td({ children }: { children: React.ReactNode }) {
  return <td className="max-w-sm px-4 py-4 align-top text-slate-700">{children}</td>;
}

function cleanFilters<T extends Record<string, string>>(
  filters: T,
): Partial<T> {
  const cleaned: Partial<T> = {};

  for (const [key, value] of Object.entries(filters) as [keyof T, string][]) {
    if (value.trim()) {
      cleaned[key] = value.trim() as T[keyof T];
    }
  }

  return cleaned;
}

function formatDate(value: string): string {
  return new Date(value).toLocaleString();
}

function formatBytes(value: number): string {
  if (value < 1024) {
    return `${value} B`;
  }

  if (value < 1024 * 1024) {
    return `${(value / 1024).toFixed(1)} KB`;
  }

  if (value < 1024 * 1024 * 1024) {
    return `${(value / (1024 * 1024)).toFixed(1)} MB`;
  }

  return `${(value / (1024 * 1024 * 1024)).toFixed(1)} GB`;
}

function payloadPreview(payload: Record<string, unknown>): string {
  const serialized = JSON.stringify(payload);

  if (serialized.length <= 160) {
    return serialized;
  }

  return `${serialized.slice(0, 157)}...`;
}
