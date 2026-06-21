"use client";

import { useCallback, useEffect, useState } from "react";
import { DashboardShell } from "../layout/dashboard-shell";
import { Button } from "../ui/button";
import { ErrorState } from "../ui/error-state";
import { LoadingState } from "../ui/loading-state";
import { PageHeader } from "../ui/page-header";
import { UploadDropzone } from "../upload/upload-dropzone";
import { JobProgressCards } from "../upload/job-progress-cards";
import { DocumentTable } from "../documents/document-table";
import { listDocuments, WorkspaceDocument } from "../../lib/upload-api";

type WorkspaceUploadManagerProps = {
  workspaceId: string;
};

export function WorkspaceUploadManager({
  workspaceId,
}: WorkspaceUploadManagerProps) {
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
      activeItem="overview"
      title="Workspace overview"
      description="Upload, index, review, and query documents from one operational console."
      workspaceId={workspaceId}
    >
      <PageHeader
        kicker="Workspace"
        title="Your document operations hub"
        description="Track ingestion health, add source files, and move quickly into grounded chat or review workflows."
        meta={
          <p className="font-mono text-xs text-muted-foreground">
            {workspaceId}
          </p>
        }
        actions={
          <>
            <Button href={`/chat/${workspaceId}`}>Open chat</Button>
            <Button href={`/usage/${workspaceId}`} variant="secondary">
              View usage
            </Button>
          </>
        }
      />

      <div className="grid gap-6">
        <JobProgressCards documents={documents} />

        <UploadDropzone
          workspaceId={workspaceId}
          onUploaded={() => void refreshDocuments()}
        />

        <section className="rounded-3xl bg-card p-5 shadow-sm ring-1 ring-border/70">
          <div className="grid gap-3 md:grid-cols-[1fr_220px_auto]">
            <input
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Search by title or source type..."
              className="rounded-xl border border-input bg-background px-4 py-2.5 text-sm outline-none transition focus:ring-2 focus:ring-ring"
            />

            <select
              value={status}
              onChange={(event) => setStatus(event.target.value)}
              className="rounded-xl border border-input bg-background px-4 py-2.5 text-sm outline-none transition focus:ring-2 focus:ring-ring"
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

        {isLoading ? (
          <LoadingState title="Loading documents" />
        ) : (
          <DocumentTable documents={documents} />
        )}
      </div>
    </DashboardShell>
  );
}
