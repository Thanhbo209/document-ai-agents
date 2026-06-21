"use client";

import { WorkspaceDocument } from "../../lib/upload-api";
import { formatDate, formatBytes, humanizeSourceType } from "../../lib/format";
import { getFileExtension } from "../../lib/file-icons";
import { FileTypeBadge } from "./document-file-icon";
import { StatusBadge } from "../ui/status-badge";
import { Button } from "../ui/button";

type DocumentCardProps = {
  document: WorkspaceDocument;
  workspaceId: string;
};

/**
 * Rich document card — shows all meaningful document metadata
 * without exposing raw IDs (document_id, workspace_id, chunk_id, etc.).
 */
export function DocumentCard({ document, workspaceId }: DocumentCardProps) {
  const primaryFile = document.files[0];
  const filename = primaryFile?.filename ?? document.title;
  const ext = getFileExtension(filename);
  const fileSizeBytes = primaryFile?.size_bytes;

  return (
    <article className="group flex flex-col overflow-hidden rounded-3xl bg-card shadow-sm ring-1 ring-border/70 transition duration-200 hover:-translate-y-1 hover:shadow-md">
      {/* Card header */}
      <div className="flex items-start gap-4 p-5">
        <FileTypeBadge ext={ext || document.source_type} size={44} />

        <div className="min-w-0 flex-1">
          <p
            className="truncate text-base font-semibold leading-tight text-card-foreground"
            title={document.title}
          >
            {document.title}
          </p>
          {filename !== document.title && (
            <p
              className="mt-0.5 truncate text-xs text-muted-foreground"
              title={filename}
            >
              {filename}
            </p>
          )}
        </div>

        <StatusBadge status={document.status} />
      </div>

      {/* Metadata row */}
      <div className="mx-5 border-t border-border/60 py-4">
        <dl className="grid grid-cols-2 gap-3 text-sm sm:grid-cols-3">
          <MetaItem
            label="File type"
            value={humanizeSourceType(ext || document.source_type)}
          />
          <MetaItem
            label="Chunks"
            value={
              document.chunk_count > 0
                ? `${document.chunk_count.toLocaleString()} indexed`
                : "Not indexed"
            }
          />
          {fileSizeBytes !== undefined && (
            <MetaItem label="Size" value={formatBytes(fileSizeBytes)} />
          )}
          <MetaItem label="Added" value={formatDate(document.created_at)} />
          <MetaItem label="Updated" value={formatDate(document.updated_at)} />
          {document.latest_job && (
            <div className="flex flex-col gap-1">
              <dt className="text-xs text-muted-foreground">Latest job</dt>
              <dd>
                <StatusBadge status={document.latest_job.status} />
              </dd>
            </div>
          )}
        </dl>

        {document.latest_job?.error_message && (
          <p className="mt-3 rounded-xl bg-destructive/10 px-3 py-2 text-xs leading-5 text-destructive">
            {document.latest_job.error_message}
          </p>
        )}
      </div>

      {/* Actions */}
      <div className="mt-auto flex gap-2 border-t border-border/60 p-4">
        <Button
          href={`/chat/${workspaceId}`}
          variant="secondary"
          className="flex-1 text-xs"
        >
          Ask about this
        </Button>
      </div>
    </article>
  );
}

function MetaItem({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex flex-col gap-0.5">
      <dt className="text-xs text-muted-foreground">{label}</dt>
      <dd className="text-sm font-medium text-card-foreground">{value}</dd>
    </div>
  );
}
