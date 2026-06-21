"use client";

import { useCallback, useEffect, useState } from "react";
import { listDocuments, WorkspaceDocument } from "../../lib/upload-api";
import { DashboardShell } from "../layout/dashboard-shell";
import { Button } from "../ui/button";
import { ErrorState } from "../ui/error-state";
import { PageHeader } from "../ui/page-header";
import { UploadDropzone } from "../upload/upload-dropzone";
import { DocumentCardGrid } from "./document-card-grid";

type DocumentsManagerProps = {
  workspaceId: string;
};

export function DocumentsManager({ workspaceId }: DocumentsManagerProps) {
  const [documents, setDocuments] = useState<WorkspaceDocument[]>([]);
  const [query, setQuery] = useState("");
  const [status, setStatus] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const refreshDocuments = useCallback(async () => {
    setIsLoading(true);
    setErrorMessage(null);

    try {
      const response = await listDocuments(workspaceId, {
        query: query || undefined,
        status: status || undefined,
      });
      setDocuments(response.documents);
    } catch (error) {
      setErrorMessage(
        error instanceof Error ? error.message : "Could not load documents.",
      );
    } finally {
      setIsLoading(false);
    }
  }, [workspaceId, query, status]);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    void refreshDocuments();
  }, [refreshDocuments]);

  return (
    <DashboardShell
      activeItem="documents"
      title="Documents"
      description="Browse, search, and manage all documents indexed in this workspace."
      workspaceId={workspaceId}
    >
      <PageHeader
        kicker="Document library"
        title="Your indexed sources"
        description="All uploaded files are chunked and indexed for grounded chat. Search or filter by status to find what you need."
        actions={
          <Button href={`/chat/${workspaceId}`}>Open chat</Button>
        }
      />

      <div className="grid gap-6">
        {/* Upload dropzone */}
        <UploadDropzone
          workspaceId={workspaceId}
          onUploaded={() => void refreshDocuments()}
        />

        {/* Search and filter bar */}
        <section className="rounded-3xl bg-card p-5 shadow-sm ring-1 ring-border/70">
          <div className="grid gap-3 sm:grid-cols-[1fr_200px_auto]">
            <input
              id="document-search"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Search by title or filename..."
              className="rounded-xl border border-input bg-background px-4 py-2.5 text-sm outline-none transition focus:ring-2 focus:ring-ring"
              aria-label="Search documents"
            />

            <select
              id="document-status-filter"
              value={status}
              onChange={(event) => setStatus(event.target.value)}
              className="rounded-xl border border-input bg-background px-4 py-2.5 text-sm outline-none transition focus:ring-2 focus:ring-ring"
              aria-label="Filter by status"
            >
              <option value="">All statuses</option>
              <option value="created">Created</option>
              <option value="processing">Processing</option>
              <option value="indexed">Indexed</option>
              <option value="failed">Failed</option>
            </select>

            <Button onClick={() => void refreshDocuments()}>Refresh</Button>
          </div>

          {errorMessage && (
            <div className="mt-4">
              <ErrorState message={errorMessage} />
            </div>
          )}
        </section>

        {/* Document cards */}
        <DocumentCardGrid
          documents={documents}
          workspaceId={workspaceId}
          isLoading={isLoading}
          errorMessage={errorMessage && !isLoading ? errorMessage : null}
          onRetry={() => void refreshDocuments()}
        />
      </div>
    </DashboardShell>
  );
}
