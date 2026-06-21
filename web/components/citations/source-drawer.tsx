import { QuerySource } from "../../lib/chat-api";
import {
  formatCitationLabel,
  formatMetadataTimestamp,
  formatSourceMetadataSummary,
} from "../../lib/citations";
import { Button } from "../ui/button";

type SourceDrawerProps = {
  source: QuerySource | null;
  onClose: () => void;
};

export function SourceDrawer({ source, onClose }: SourceDrawerProps) {
  if (!source) {
    return null;
  }

  const timestamp = formatMetadataTimestamp(source.metadata);
  const sourceSummary = formatSourceMetadataSummary(source.metadata);

  return (
    <aside className="fixed inset-y-0 right-0 z-50 w-full max-w-xl border-l border-border bg-card shadow-2xl">
      <div className="flex items-start justify-between border-b border-border px-6 py-4">
        <div>
          <p className="text-sm font-medium text-muted-foreground">
            {formatCitationLabel(source.source_id)}
          </p>
          <h2 className="mt-1 text-lg font-semibold text-card-foreground">
            Citation context
          </h2>
          {sourceSummary && (
            <p className="mt-1 text-sm text-muted-foreground">{sourceSummary}</p>
          )}
        </div>

        <Button variant="secondary" onClick={onClose}>
          Close
        </Button>
      </div>

      <div className="space-y-5 overflow-y-auto px-6 py-5">
        <div className="rounded-2xl bg-muted p-4 text-sm">
          <dl className="grid gap-3">
            <div>
              <dt className="font-medium text-muted-foreground">Document ID</dt>
              <dd className="mt-1 font-mono text-xs text-card-foreground">
                {source.document_id}
              </dd>
            </div>

            <div>
              <dt className="font-medium text-muted-foreground">Chunk ID</dt>
              <dd className="mt-1 font-mono text-xs text-card-foreground">
                {source.chunk_id}
              </dd>
            </div>

            <div className="grid grid-cols-3 gap-3">
              {timestamp && (
                <div>
                  <dt className="font-medium text-muted-foreground">Timestamp</dt>
                  <dd className="mt-1 text-card-foreground">{timestamp}</dd>
                </div>
              )}

              <div>
                <dt className="font-medium text-muted-foreground">Page</dt>
                <dd className="mt-1 text-card-foreground">
                  {source.source_page ?? "N/A"}
                </dd>
              </div>

              <div>
                <dt className="font-medium text-muted-foreground">Start</dt>
                <dd className="mt-1 text-card-foreground">
                  {source.source_start_offset ?? "N/A"}
                </dd>
              </div>

              <div>
                <dt className="font-medium text-muted-foreground">End</dt>
                <dd className="mt-1 text-card-foreground">
                  {source.source_end_offset ?? "N/A"}
                </dd>
              </div>
            </div>

            <div>
              <dt className="font-medium text-muted-foreground">Score</dt>
              <dd className="mt-1 text-card-foreground">
                {source.score.toFixed(3)}
              </dd>
            </div>
          </dl>
        </div>

        <div>
          <h3 className="text-sm font-semibold text-card-foreground">
            Source span
          </h3>
          <pre className="mt-3 whitespace-pre-wrap rounded-2xl bg-primary p-4 text-sm leading-6 text-primary-foreground">
            {source.text}
          </pre>
        </div>
      </div>
    </aside>
  );
}
