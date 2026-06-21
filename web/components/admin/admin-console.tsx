"use client";

import { ReactNode, useCallback, useEffect, useMemo, useState } from "react";
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
import { buildAdminNavItems, DashboardShell } from "../layout/dashboard-shell";
import { Button } from "../ui/button";
import { EmptyState } from "../ui/empty-state";
import { ErrorState } from "../ui/error-state";
import { LoadingState } from "../ui/loading-state";
import { PageHeader } from "../ui/page-header";
import { StatCard } from "../ui/stat-card";
import { StatusBadge } from "../ui/status-badge";

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

  const adminNavItems = useMemo(
    () => buildAdminNavItems((item) => setActiveTab(item)),
    [],
  );

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

  const failedJobs = jobs.filter((job) => job.status === "failed").length;
  const storageBytes = workspaces.reduce(
    (total, workspace) => total + workspace.storage_bytes,
    0,
  );

  return (
    <DashboardShell
      activeItem={activeTab}
      title="Support console"
      description="Inspect tenant metadata, failed jobs, billing plan data, and audit events without exposing private document content."
      mode="admin"
      navItems={adminNavItems}
    >
      <PageHeader
        kicker="Platform admin"
        title="Operations without crossing the privacy boundary"
        description="Review tenant health, failed ingestion work, and security events. Document text, chunk text, file contents, and conversation content stay out of this console."
        actions={<Button onClick={() => void refreshAll()}>Refresh data</Button>}
      />

      {errorMessage && (
        <div className="mb-6">
          <ErrorState message={errorMessage} />
        </div>
      )}

      <section className="mb-6 grid grid-flow-dense gap-4 md:grid-cols-4">
        <StatCard
          label="Workspaces"
          value={workspaces.length}
          detail="Tenants visible to support"
        />
        <StatCard
          label="Failed jobs"
          value={failedJobs}
          detail="Ingestion failures in view"
          tone={failedJobs > 0 ? "danger" : "neutral"}
        />
        <StatCard
          label="Storage"
          value={formatBytes(storageBytes)}
          detail="Uploaded source bytes"
        />
        <StatCard
          label="Audit events"
          value={auditEvents.length}
          detail="Current search result count"
        />
      </section>

      {isLoading ? (
        <LoadingState title="Loading admin console" />
      ) : (
        <>
          <div className="mb-6 flex flex-wrap gap-2">
            <SegmentButton
              label="Workspaces"
              isActive={activeTab === "workspaces"}
              onClick={() => setActiveTab("workspaces")}
            />
            <SegmentButton
              label="Jobs"
              isActive={activeTab === "jobs"}
              onClick={() => setActiveTab("jobs")}
            />
            <SegmentButton
              label="Audit events"
              isActive={activeTab === "audit"}
              onClick={() => setActiveTab("audit")}
            />
          </div>

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
    </DashboardShell>
  );
}

function SegmentButton({
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
      className={[
        "rounded-xl px-4 py-2.5 text-sm font-medium transition duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
        isActive
          ? "bg-primary text-primary-foreground shadow-sm"
          : "border border-border bg-card text-muted-foreground hover:-translate-y-0.5 hover:bg-accent hover:text-accent-foreground",
      ].join(" ")}
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
      {workspaces.length === 0 ? (
        <EmptyState
          title="No workspaces found"
          description="Registered tenant metadata will appear here."
        />
      ) : (
        <TableShell title="Workspace inventory">
          <table className="min-w-[64rem] divide-y divide-border text-sm">
            <thead className="bg-muted/70 text-left text-xs font-medium text-muted-foreground">
              <tr>
              <Th>Workspace</Th>
              <Th>Owner</Th>
              <Th>Status</Th>
              <Th>Documents</Th>
              <Th>Failed jobs</Th>
                <Th>Storage</Th>
                <Th>Plan</Th>
                <Th>Created</Th>
                <Th>Metadata</Th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border/70 bg-card">
              {workspaces.map((workspace) => (
                <tr key={workspace.id} className="transition hover:bg-accent/50">
                  <Td>
                    <div className="font-medium text-card-foreground">
                      {workspace.name}
                    </div>
                    <Mono>{workspace.id}</Mono>
                  </Td>
                  <Td>
                    <div>{workspace.owner_email}</div>
                    <Mono>{workspace.owner_user_id}</Mono>
                  </Td>
                  <Td>
                    <StatusBadge status={workspace.status} />
                  </Td>
                  <Td>{workspace.document_count.toLocaleString()}</Td>
                  <Td>
                    <StatusBadge status={`${workspace.failed_job_count} failed`} />
                  </Td>
                  <Td>{formatBytes(workspace.storage_bytes)}</Td>
                  <Td>
                    <StatusBadge status={workspace.plan_name} />
                  </Td>
                  <Td>{formatDate(workspace.created_at)}</Td>
                  <Td>
                    <Button
                      variant="secondary"
                      onClick={() => onLoadDocuments(workspace.id)}
                    >
                      View documents
                    </Button>
                  </Td>
                </tr>
              ))}
            </tbody>
          </table>
        </TableShell>
      )}

      {selectedWorkspaceId && (
        <section className="rounded-3xl bg-card p-5 shadow-sm ring-1 ring-border/70">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div>
              <p className="text-sm font-medium text-muted-foreground">
                Document metadata
              </p>
              <h2 className="mt-1 text-xl font-semibold tracking-tight text-card-foreground">
                Metadata-only inventory
              </h2>
              <Mono>{selectedWorkspaceId}</Mono>
            </div>
            <p className="max-w-md text-sm leading-6 text-muted-foreground">
              This view intentionally excludes raw text, chunk text, uploaded
              file content, and conversation messages.
            </p>
          </div>

          <div className="mt-5 overflow-x-auto">
            {documents.length === 0 ? (
              <EmptyState
                title="No document metadata"
                description="This workspace has no document records yet."
              />
            ) : (
              <table className="min-w-[48rem] divide-y divide-border text-sm">
                <thead className="bg-muted/70 text-left text-xs font-medium text-muted-foreground">
                  <tr>
                    <Th>Title</Th>
                    <Th>Status</Th>
                    <Th>Source</Th>
                    <Th>Files</Th>
                    <Th>Chunks</Th>
                    <Th>Updated</Th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border/70">
                  {documents.map((document) => (
                    <tr
                      key={document.id}
                      className="transition hover:bg-accent/50"
                    >
                      <Td>
                        <div className="font-medium text-card-foreground">
                          {document.title}
                        </div>
                        <Mono>{document.id}</Mono>
                      </Td>
                      <Td>
                        <StatusBadge status={document.status} />
                      </Td>
                      <Td>{document.source_type}</Td>
                      <Td>{document.file_count}</Td>
                      <Td>{document.chunk_count}</Td>
                      <Td>{formatDate(document.updated_at)}</Td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
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
      <div className="grid gap-3 rounded-3xl bg-card p-5 shadow-sm ring-1 ring-border/70 md:grid-cols-[1fr_220px_auto]">
        <input
          value={filters.workspace_id}
          onChange={(event) =>
            onChangeFilters({ ...filters, workspace_id: event.target.value })
          }
          placeholder="Workspace ID"
          className="rounded-xl border border-input bg-background px-4 py-2.5 text-sm outline-none transition focus:ring-2 focus:ring-ring"
        />
        <select
          value={filters.status}
          onChange={(event) =>
            onChangeFilters({ ...filters, status: event.target.value })
          }
          className="rounded-xl border border-input bg-background px-4 py-2.5 text-sm outline-none transition focus:ring-2 focus:ring-ring"
        >
          <option value="">All statuses</option>
          <option value="queued">Queued</option>
          <option value="processing">Processing</option>
          <option value="succeeded">Succeeded</option>
          <option value="failed">Failed</option>
        </select>
        <Button onClick={onSearch}>Search jobs</Button>
      </div>

      {jobs.length === 0 ? (
        <EmptyState
          title="No jobs match these filters"
          description="Clear the status or workspace filters to inspect more ingestion jobs."
        />
      ) : (
        <TableShell title="Ingestion jobs">
          <table className="min-w-[64rem] divide-y divide-border text-sm">
            <thead className="bg-muted/70 text-left text-xs font-medium text-muted-foreground">
              <tr>
                <Th>Job</Th>
                <Th>Workspace</Th>
                <Th>Document</Th>
                <Th>Status</Th>
                <Th>Error</Th>
                <Th>Updated</Th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border/70 bg-card">
              {jobs.map((job) => (
                <tr key={job.id} className="transition hover:bg-accent/50">
                  <Td>
                    <Mono>{job.id}</Mono>
                  </Td>
                  <Td>
                    <Mono>{job.workspace_id}</Mono>
                  </Td>
                  <Td>
                    <Mono>{job.document_id}</Mono>
                  </Td>
                  <Td>
                    <StatusBadge status={job.status} />
                  </Td>
                  <Td>
                    <span className="max-w-md text-muted-foreground">
                      {job.error_message ?? "-"}
                    </span>
                  </Td>
                  <Td>{formatDate(job.updated_at)}</Td>
                </tr>
              ))}
            </tbody>
          </table>
        </TableShell>
      )}
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
      <div className="grid gap-3 rounded-3xl bg-card p-5 shadow-sm ring-1 ring-border/70 lg:grid-cols-[1fr_1fr_1fr_auto]">
        <input
          value={filters.workspace_id}
          onChange={(event) =>
            onChangeFilters({ ...filters, workspace_id: event.target.value })
          }
          placeholder="Workspace ID"
          className="rounded-xl border border-input bg-background px-4 py-2.5 text-sm outline-none transition focus:ring-2 focus:ring-ring"
        />
        <input
          value={filters.event_type}
          onChange={(event) =>
            onChangeFilters({ ...filters, event_type: event.target.value })
          }
          placeholder="Event type"
          className="rounded-xl border border-input bg-background px-4 py-2.5 text-sm outline-none transition focus:ring-2 focus:ring-ring"
        />
        <input
          value={filters.actor_user_id}
          onChange={(event) =>
            onChangeFilters({ ...filters, actor_user_id: event.target.value })
          }
          placeholder="Actor user ID"
          className="rounded-xl border border-input bg-background px-4 py-2.5 text-sm outline-none transition focus:ring-2 focus:ring-ring"
        />
        <Button onClick={onSearch}>Search events</Button>
      </div>

      <div className="flex flex-wrap gap-2">
        <Button variant="secondary" onClick={() => onExport("csv")}>
          Export audit CSV
        </Button>
        <Button variant="secondary" onClick={() => onExport("json")}>
          Export audit JSON
        </Button>
      </div>

      {events.length === 0 ? (
        <EmptyState
          title="No audit events match"
          description="Adjust the event, workspace, or actor filters to broaden the audit search."
        />
      ) : (
        <TableShell title="Audit event trail">
          <table className="min-w-[70rem] divide-y divide-border text-sm">
            <thead className="bg-muted/70 text-left text-xs font-medium text-muted-foreground">
              <tr>
                <Th>Event</Th>
                <Th>Workspace</Th>
                <Th>Actor</Th>
                <Th>Entity</Th>
                <Th>Created</Th>
                <Th>Payload preview</Th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border/70 bg-card">
              {events.map((event) => (
                <tr key={event.id} className="transition hover:bg-accent/50">
                  <Td>
                    <span className="font-medium text-card-foreground">
                      {event.event_type}
                    </span>
                  </Td>
                  <Td>
                    <Mono>{event.workspace_id}</Mono>
                  </Td>
                  <Td>
                    <Mono>{event.actor_user_id ?? "-"}</Mono>
                  </Td>
                  <Td>
                    <div>{event.entity_type}</div>
                    <Mono>{event.entity_id ?? "-"}</Mono>
                  </Td>
                  <Td>{formatDate(event.created_at)}</Td>
                  <Td>
                    <code className="block max-w-md truncate rounded-xl bg-muted px-3 py-2 text-xs text-muted-foreground">
                      {payloadPreview(event.payload)}
                    </code>
                  </Td>
                </tr>
              ))}
            </tbody>
          </table>
        </TableShell>
      )}
    </section>
  );
}

function TableShell({
  title,
  children,
}: {
  title: string;
  children: ReactNode;
}) {
  return (
    <section className="overflow-hidden rounded-3xl bg-card shadow-sm ring-1 ring-border/70">
      <div className="border-b border-border px-5 py-4">
        <h2 className="text-lg font-semibold tracking-tight text-card-foreground">
          {title}
        </h2>
      </div>
      <div className="overflow-x-auto">{children}</div>
    </section>
  );
}

function Th({ children }: { children: ReactNode }) {
  return <th className="px-5 py-3">{children}</th>;
}

function Td({ children }: { children: ReactNode }) {
  return (
    <td className="max-w-sm px-5 py-4 align-top text-muted-foreground">
      {children}
    </td>
  );
}

function Mono({ children }: { children: ReactNode }) {
  return (
    <span className="mt-1 block break-all font-mono text-xs text-muted-foreground">
      {children}
    </span>
  );
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
  const serialized = JSON.stringify(redactPrivateFields(payload));

  if (serialized.length <= 160) {
    return serialized;
  }

  return `${serialized.slice(0, 157)}...`;
}

function redactPrivateFields(value: unknown): unknown {
  if (Array.isArray(value)) {
    return value.map((item) => redactPrivateFields(item));
  }

  if (value && typeof value === "object") {
    return Object.fromEntries(
      Object.entries(value).map(([key, item]) => [
        key,
        privatePayloadKeys.has(key.toLowerCase())
          ? "[redacted in preview]"
          : redactPrivateFields(item),
      ]),
    );
  }

  return value;
}

const privatePayloadKeys = new Set([
  "text",
  "content",
  "source_text",
  "chunk_text",
  "message_content",
  "file_content",
]);
