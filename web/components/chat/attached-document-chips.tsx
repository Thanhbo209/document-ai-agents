"use client";

import { WorkspaceDocument } from "../../lib/upload-api";
import { getFileExtension } from "../../lib/file-icons";
import { FileTypeBadge } from "../documents/document-file-icon";

type AttachedDocumentChipsProps = {
  documents: WorkspaceDocument[];
  onRemove?: (documentId: string) => void;
  compact?: boolean;
};

export function AttachedDocumentChips({
  documents,
  onRemove,
  compact = false,
}: AttachedDocumentChipsProps) {
  if (documents.length === 0) {
    return null;
  }

  return (
    <div className="flex flex-wrap gap-2">
      {documents.map((document) => {
        const filename = document.files[0]?.filename ?? document.title;
        const ext = getFileExtension(filename) || document.source_type;

        return (
          <span
            key={document.id}
            className={[
              "inline-flex max-w-full items-center gap-2 rounded-xl border border-border bg-background text-muted-foreground",
              compact ? "px-2 py-1 text-[11px]" : "px-3 py-1.5 text-xs",
            ].join(" ")}
            title={document.title}
          >
            <FileTypeBadge ext={ext} size={compact ? 20 : 24} />
            <span className="truncate">{document.title}</span>
            {onRemove && (
              <button
                type="button"
                onClick={() => onRemove(document.id)}
                className="shrink-0 rounded-full px-1 text-muted-foreground transition hover:bg-accent hover:text-accent-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                aria-label={`Remove ${document.title}`}
              >
                ×
              </button>
            )}
          </span>
        );
      })}
    </div>
  );
}
