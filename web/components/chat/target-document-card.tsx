import { WorkspaceDocument } from "../../lib/upload-api";
import { getFileExtension } from "../../lib/file-icons";
import { FileTypeBadge } from "../documents/document-file-icon";
import { StatusBadge } from "../ui/status-badge";
import { humanizeSourceType } from "../../lib/format";

type TargetDocumentCardProps = {
  document: WorkspaceDocument;
  isSelected: boolean;
  onToggle: () => void;
};

/**
 * Compact selectable document card for the Chat page's retrieval scope panel.
 * Shows file icon, title, type, status and chunks — no raw IDs.
 */
export function TargetDocumentCard({
  document,
  isSelected,
  onToggle,
}: TargetDocumentCardProps) {
  const filename = document.files[0]?.filename ?? document.title;
  const ext = getFileExtension(filename);

  return (
    <label
      className={[
        "group flex cursor-pointer items-start gap-3 rounded-2xl border p-3 transition duration-200",
        "hover:-translate-y-0.5 focus-within:ring-2 focus-within:ring-ring",
        isSelected
          ? "border-primary/40 bg-primary/8 shadow-sm"
          : "border-border bg-background/70 hover:bg-accent",
      ].join(" ")}
    >
      <input
        type="checkbox"
        checked={isSelected}
        onChange={onToggle}
        className="mt-1 accent-primary"
        aria-label={`Select ${document.title}`}
      />

      <div className="flex min-w-0 flex-1 items-start gap-2.5">
        <FileTypeBadge ext={ext || document.source_type} size={28} />

        <span className="min-w-0 flex-1">
          <span className="block truncate text-sm font-medium text-card-foreground">
            {document.title}
          </span>
          <span className="mt-1 flex flex-wrap items-center gap-1.5 text-xs text-muted-foreground">
            <StatusBadge status={document.status} />
            <span>{humanizeSourceType(ext || document.source_type)}</span>
            {document.chunk_count > 0 && (
              <span>{document.chunk_count.toLocaleString()} chunks</span>
            )}
          </span>
        </span>
      </div>
    </label>
  );
}
