import { WorkspaceDocument } from "../../lib/upload-api";
import { getFileExtension } from "../../lib/file-icons";
import { FileTypeBadge } from "./document-file-icon";
import { EmptyState } from "../ui/empty-state";
import { StatusBadge } from "../ui/status-badge";

type DocumentTableProps = {
  documents: WorkspaceDocument[];
};

export function DocumentTable({ documents }: DocumentTableProps) {
  return (
    <section className="overflow-hidden rounded-3xl bg-card shadow-sm ring-1 ring-border/70">
      <div className="border-b border-border px-6 py-5">
        <h2 className="text-lg font-semibold text-card-foreground">
          Document library
        </h2>
        <p className="mt-1 text-sm text-muted-foreground">
          Search metadata, inspect status, and review failed ingestion causes.
        </p>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full min-w-[56rem] text-left text-sm">
          <thead className="bg-muted/70 text-xs font-medium text-muted-foreground">
            <tr>
              <th className="px-6 py-3">Title</th>
              <th className="px-6 py-3">Source</th>
              <th className="px-6 py-3">Status</th>
              <th className="px-6 py-3">Chunks</th>
              <th className="px-6 py-3">File</th>
              <th className="px-6 py-3">Latest job</th>
              <th className="px-6 py-3">Updated</th>
            </tr>
          </thead>

          <tbody className="divide-y divide-border/70">
            {documents.map((document) => {
              const filename = document.files[0]?.filename ?? document.title;
              const ext = getFileExtension(filename);

              return (
                <tr
                  key={document.id}
                  className="align-top transition hover:bg-accent/50"
                >
                  <td className="px-6 py-4">
                    <p className="font-medium text-card-foreground">
                      {document.title}
                    </p>
                    <p className="mt-1 font-mono text-xs text-muted-foreground">
                      {document.id}
                    </p>
                  </td>

                  <td className="px-6 py-4">
                    <FileTypeBadge ext={ext || document.source_type} size={32} />
                  </td>

                  <td className="px-6 py-4">
                    <StatusBadge status={document.status} />
                  </td>

                  <td className="px-6 py-4 font-mono text-muted-foreground">
                    {document.chunk_count}
                  </td>

                  <td className="px-6 py-4 text-muted-foreground">
                    {filename}
                  </td>

                  <td className="px-6 py-4">
                    {document.latest_job ? (
                      <div>
                        <StatusBadge status={document.latest_job.status} />
                        {document.latest_job.error_message && (
                          <p className="mt-2 max-w-xs text-xs leading-5 text-destructive">
                            {document.latest_job.error_message}
                          </p>
                        )}
                      </div>
                    ) : (
                      <span className="text-muted-foreground">No job</span>
                    )}
                  </td>

                  <td className="px-6 py-4 text-muted-foreground">
                    {new Date(document.updated_at).toLocaleString()}
                  </td>
                </tr>
              );
            })}

            {documents.length === 0 && (
              <tr>
                <td colSpan={7} className="px-6 py-10">
                  <EmptyState
                    title="No documents match this view"
                    description="Upload a source file or adjust the search and status filters to widen the result set."
                  />
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </section>
  );
}
