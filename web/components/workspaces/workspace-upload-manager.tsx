"use client";

import { useCallback, useEffect, useState } from "react";
import { UploadDropzone } from "../upload/upload-dropzone";
import { JobProgressCards } from "../upload/job-progress-cards";
import { DocumentTable } from "../documents/document-table";
import { listDocuments, WorkspaceDocument } from "../../lib/upload-api";
import Link from "next/link";

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
    <div className="mx-auto max-w-7xl px-6 py-8">
      <header className="mb-8">
        <p className="text-sm font-medium text-slate-500">Workspace</p>
        <h1 className="mt-2 text-3xl font-bold tracking-tight text-slate-950">
          Upload Manager
        </h1>
        <p className="mt-2 max-w-2xl text-slate-600">
          Upload documents, monitor ingestion jobs, inspect failures, and search
          document metadata.
        </p>
        <p className="mt-3 font-mono text-xs text-slate-400">{workspaceId}</p>
        <Link
          href={`/chat/${workspaceId}`}
          className="mt-4 inline-flex rounded-lg bg-slate-950 px-4 py-2 text-sm font-medium text-white"
        >
          Open chat
        </Link>
      </header>

      <div className="grid gap-6">
        <UploadDropzone
          workspaceId={workspaceId}
          onUploaded={() => void refreshDocuments()}
        />

        <JobProgressCards documents={documents} />

        <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
          <div className="grid gap-4 md:grid-cols-[1fr_220px_auto]">
            <input
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Search by title or source type..."
              className="rounded-lg border border-slate-300 px-4 py-2 text-sm outline-none ring-slate-900 focus:ring-2"
            />

            <select
              value={status}
              onChange={(event) => setStatus(event.target.value)}
              className="rounded-lg border border-slate-300 px-4 py-2 text-sm outline-none ring-slate-900 focus:ring-2"
            >
              <option value="">All statuses</option>
              <option value="created">Created</option>
              <option value="processing">Processing</option>
              <option value="indexed">Indexed</option>
              <option value="failed">Failed</option>
            </select>

            <button
              type="button"
              onClick={() => void refreshDocuments()}
              className="rounded-lg bg-slate-950 px-5 py-2 text-sm font-medium text-white"
            >
              Refresh
            </button>
          </div>

          {errorMessage && (
            <p className="mt-4 rounded-lg bg-red-50 px-4 py-3 text-sm text-red-700">
              {errorMessage}
            </p>
          )}
        </section>

        {isLoading ? (
          <div className="rounded-2xl border border-slate-200 bg-white p-10 text-center text-slate-500 shadow-sm">
            Loading documents...
          </div>
        ) : (
          <DocumentTable documents={documents} />
        )}
      </div>
    </div>
  );
}
