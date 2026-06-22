"use client";

import { useMemo, useState } from "react";
import { getFileExtension } from "../../lib/file-icons";
import { formatBytes, formatDate } from "../../lib/format";
import { WorkspaceDocument } from "../../lib/upload-api";
import { FileTypeBadge } from "../documents/document-file-icon";
import { Button } from "../ui/button";
import { EmptyState } from "../ui/empty-state";
import { LoadingState } from "../ui/loading-state";
import { StatusBadge } from "../ui/status-badge";

type DocumentAttachModalProps = {
  isOpen: boolean;
  documents: WorkspaceDocument[];
  selectedIds: string[];
  isLoading: boolean;
  onClose: () => void;
  onAttach: (documentIds: string[]) => void;
};

const SOURCE_FILTERS = [
  { value: "", label: "All sources" },
  { value: "documents", label: "Documents" },
  { value: "tables", label: "Tables" },
  { value: "media", label: "Media" },
  { value: "web", label: "Web and YouTube" },
  { value: "repo", label: "Repositories" },
];

export function DocumentAttachModal({
  isOpen,
  documents,
  selectedIds,
  isLoading,
  onClose,
  onAttach,
}: DocumentAttachModalProps) {
  const [draftSelectedIds, setDraftSelectedIds] = useState<string[]>(selectedIds);
  const [query, setQuery] = useState("");
  const [sourceFilter, setSourceFilter] = useState("");

  const filteredDocuments = useMemo(
    () =>
      documents.filter((document) => {
        const searchTarget = [
          document.title,
          document.source_type,
          document.files.map((file) => file.filename).join(" "),
        ]
          .join(" ")
          .toLowerCase();
        const matchesQuery = searchTarget.includes(query.trim().toLowerCase());
        const matchesFilter =
          !sourceFilter || sourceGroup(document.source_type) === sourceFilter;
        return matchesQuery && matchesFilter;
      }),
    [documents, query, sourceFilter],
  );

  if (!isOpen) {
    return null;
  }

  function toggleDocument(document: WorkspaceDocument) {
    if (!isAttachable(document)) {
      return;
    }

    setDraftSelectedIds((current) =>
      current.includes(document.id)
        ? current.filter((id) => id !== document.id)
        : [...current, document.id],
    );
  }

  return (
    <div className="fixed inset-0 z-50 grid place-items-center bg-black/45 px-4 py-6">
      <section className="flex max-h-[90dvh] w-full max-w-5xl flex-col overflow-hidden rounded-3xl bg-card shadow-2xl ring-1 ring-border">
        <div className="flex flex-col gap-4 border-b border-border px-5 py-4 sm:flex-row sm:items-start sm:justify-between">
          <div>
            <p className="text-sm font-medium text-muted-foreground">
              Attach context
            </p>
            <h2 className="mt-1 text-xl font-semibold text-card-foreground">
              Choose documents for this question
            </h2>
            <p className="mt-1 max-w-2xl text-sm leading-6 text-muted-foreground">
              Attach one or more indexed sources to limit retrieval. Leave the
              selection empty to query the whole workspace.
            </p>
          </div>
          <Button variant="secondary" onClick={onClose}>
            Close
          </Button>
        </div>

        <div className="border-b border-border p-4">
          <div className="grid gap-3 sm:grid-cols-[1fr_220px_auto]">
            <input
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Search imported documents..."
              className="rounded-xl border border-input bg-background px-4 py-2.5 text-sm outline-none transition focus:ring-2 focus:ring-ring"
              aria-label="Search imported documents"
            />
            <select
              value={sourceFilter}
              onChange={(event) => setSourceFilter(event.target.value)}
              className="rounded-xl border border-input bg-background px-4 py-2.5 text-sm outline-none transition focus:ring-2 focus:ring-ring"
              aria-label="Filter source type"
            >
              {SOURCE_FILTERS.map((filter) => (
                <option key={filter.value || "all"} value={filter.value}>
                  {filter.label}
                </option>
              ))}
            </select>
            <Button
              variant="quiet"
              onClick={() => {
                setDraftSelectedIds([]);
                setQuery("");
                setSourceFilter("");
              }}
            >
              Clear
            </Button>
          </div>
        </div>

        <div className="min-h-0 flex-1 overflow-y-auto p-4">
          {isLoading ? (
            <LoadingState title="Loading documents" rows={4} />
          ) : documents.length === 0 ? (
            <EmptyState
              title="No imported documents"
              description="Import a document before attaching context to chat."
            />
          ) : filteredDocuments.length === 0 ? (
            <EmptyState
              title="No matching documents"
              description="Try a different search or source type filter."
            />
          ) : (
            <div className="grid gap-3 md:grid-cols-2">
              {filteredDocuments.map((document) => {
                const attachable = isAttachable(document);
                const selected = draftSelectedIds.includes(document.id);
                return (
                  <button
                    key={document.id}
                    type="button"
                    disabled={!attachable}
                    onClick={() => toggleDocument(document)}
                    className={[
                      "rounded-2xl border p-4 text-left transition duration-200",
                      "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-65",
                      selected
                        ? "border-primary/60 bg-primary/10 shadow-sm"
                        : "border-border bg-background hover:-translate-y-0.5 hover:bg-accent",
                    ].join(" ")}
                    aria-pressed={selected}
                  >
                    <DocumentFileCard document={document} />
                    {!attachable && (
                      <p className="mt-3 rounded-xl bg-muted px-3 py-2 text-xs leading-5 text-muted-foreground">
                        {disabledReason(document)}
                      </p>
                    )}
                  </button>
                );
              })}
            </div>
          )}
        </div>

        <div className="flex flex-col gap-3 border-t border-border p-4 sm:flex-row sm:items-center sm:justify-between">
          <p className="text-sm text-muted-foreground">
            {draftSelectedIds.length === 0
              ? "No documents attached. The next question will search the whole workspace."
              : `${draftSelectedIds.length} ${
                  draftSelectedIds.length === 1 ? "document" : "documents"
                } selected.`}
          </p>
          <div className="flex flex-wrap gap-2">
            <Button variant="secondary" onClick={onClose}>
              Cancel
            </Button>
            <Button
              onClick={() => {
                onAttach(draftSelectedIds);
                onClose();
              }}
            >
              Attach selected
            </Button>
          </div>
        </div>
      </section>
    </div>
  );
}

function DocumentFileCard({ document }: { document: WorkspaceDocument }) {
  const primaryFile = document.files[0];
  const filename = primaryFile?.filename ?? document.title;
  const ext = getFileExtension(filename) || document.source_type;

  return (
    <div className="flex items-start gap-3">
      <FileTypeBadge ext={ext} size={40} />
      <div className="min-w-0 flex-1">
        <div className="flex flex-wrap items-start justify-between gap-2">
          <p className="truncate text-sm font-semibold text-card-foreground">
            {document.title}
          </p>
          <StatusBadge status={document.status} />
        </div>
        <div className="mt-2 flex flex-wrap gap-x-3 gap-y-1 text-xs text-muted-foreground">
          <span>{formatDate(document.created_at)}</span>
          <span>
            {document.chunk_count.toLocaleString()}{" "}
            {document.chunk_count === 1 ? "chunk" : "chunks"}
          </span>
          {primaryFile?.size_bytes !== undefined && (
            <span>{formatBytes(primaryFile.size_bytes)}</span>
          )}
        </div>
        {document.latest_job?.error_message && (
          <p className="mt-2 text-xs leading-5 text-destructive">
            {document.latest_job.error_message}
          </p>
        )}
      </div>
    </div>
  );
}

function isAttachable(document: WorkspaceDocument): boolean {
  return document.status === "indexed" && document.chunk_count > 0;
}

function disabledReason(document: WorkspaceDocument): string {
  if (document.status === "processing") {
    return "This source is still processing and cannot be attached yet.";
  }
  if (document.status === "failed") {
    return "This import failed and cannot be used as chat context.";
  }
  if (document.chunk_count === 0) {
    return "This source has no indexed chunks to retrieve from yet.";
  }
  return "This source is not ready for chat context.";
}

function sourceGroup(sourceType: string): string {
  if (["csv", "xlsx"].includes(sourceType)) return "tables";
  if (["audio", "video"].includes(sourceType)) return "media";
  if (["web", "youtube"].includes(sourceType)) return "web";
  if (sourceType === "repo") return "repo";
  return "documents";
}
