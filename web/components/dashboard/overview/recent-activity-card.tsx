import { formatRelativeTime, humanizeSourceType } from "../../../lib/format";
import { getFileExtension } from "../../../lib/file-icons";
import { FileTypeBadge } from "../../documents/document-file-icon";
import { StatusBadge } from "../../ui/status-badge";
import { SectionCard } from "../../ui/section-card";
import { Button } from "../../ui/button";
import type { WorkspaceDocument } from "../../../lib/upload-api";

type RecentActivityCardProps = {
  documents: WorkspaceDocument[];
  workspaceId: string;
};

export function RecentActivityCard({
  documents,
  workspaceId,
}: RecentActivityCardProps) {
  // Show the 5 most recently updated documents
  const recent = [...documents]
    .sort(
      (a, b) =>
        new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime(),
    )
    .slice(0, 5);

  return (
    <SectionCard>
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-sm font-medium text-muted-foreground">Recent uploads</p>
          <h3 className="mt-1 text-xl font-semibold tracking-tight text-card-foreground">
            Latest activity
          </h3>
        </div>
        <Button href={`/documents/${workspaceId}`} variant="secondary">
          View all
        </Button>
      </div>

      {recent.length === 0 ? (
        <div className="mt-6 rounded-2xl border border-dashed border-border bg-muted/40 p-8 text-center">
          <p className="text-sm font-medium text-muted-foreground">
            No documents uploaded yet
          </p>
          <p className="mt-1 text-sm text-muted-foreground">
            Upload a file to see recent activity here.
          </p>
          <div className="mt-4 flex justify-center">
            <Button href={`/documents/${workspaceId}`} variant="secondary">
              Upload a document
            </Button>
          </div>
        </div>
      ) : (
        <ul className="mt-5 divide-y divide-border/60" role="list">
          {recent.map((doc) => {
            const filename = doc.files[0]?.filename ?? doc.title;
            const ext = getFileExtension(filename);

            return (
              <li
                key={doc.id}
                className="flex items-center gap-3 py-3 first:pt-0 last:pb-0"
              >
                <FileTypeBadge ext={ext || doc.source_type} size={32} />
                <div className="min-w-0 flex-1">
                  <p className="truncate text-sm font-medium text-card-foreground">
                    {doc.title}
                  </p>
                  <p className="text-xs text-muted-foreground">
                    {humanizeSourceType(ext || doc.source_type)} ·{" "}
                    {formatRelativeTime(doc.updated_at)}
                  </p>
                </div>
                <StatusBadge status={doc.status} />
              </li>
            );
          })}
        </ul>
      )}
    </SectionCard>
  );
}
