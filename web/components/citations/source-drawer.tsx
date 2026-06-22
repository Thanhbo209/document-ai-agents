import { QuerySource } from "../../lib/chat-api";
import {
  formatCitationDetail,
  formatCitationLabel,
  formatMetadataTimestamp,
  formatSourceMetadataSummary,
} from "../../lib/citations";
import { FileTypeBadge } from "../documents/document-file-icon";
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
  const detail = formatCitationDetail(source.metadata, source.source_page);
  const facts = buildSourceFacts(source);
  const sourceType = readRawString(source.metadata, "source_type") ?? "source";

  return (
    <aside className="fixed inset-y-0 right-0 z-50 w-full max-w-xl border-l border-border bg-card shadow-2xl">
      <div className="flex items-start justify-between border-b border-border px-6 py-4">
        <div className="flex min-w-0 items-start gap-3">
          <FileTypeBadge ext={sourceType} size={40} />
          <div className="min-w-0">
            <p className="text-sm font-medium text-muted-foreground">
              {formatCitationLabel(source.source_id)}
            </p>
            <h2 className="mt-1 text-lg font-semibold text-card-foreground">
              Citation context
            </h2>
            <p className="mt-1 text-sm text-muted-foreground">
              {detail ?? sourceSummary ?? "Retrieved source context"}
            </p>
          </div>
        </div>

        <Button variant="secondary" onClick={onClose}>
          Close
        </Button>
      </div>

      <div className="space-y-5 overflow-y-auto px-6 py-5">
        <div className="rounded-2xl bg-muted p-4 text-sm">
          <dl className="grid gap-3 sm:grid-cols-2">
            {facts.map((fact) => (
              <div key={fact.label}>
                <dt className="font-medium text-muted-foreground">
                  {fact.label}
                </dt>
                <dd className="mt-1 break-words text-card-foreground">
                  {fact.value}
                </dd>
              </div>
            ))}

            {timestamp && !facts.some((fact) => fact.label === "Timestamp") && (
              <div>
                <dt className="font-medium text-muted-foreground">Timestamp</dt>
                <dd className="mt-1 text-card-foreground">{timestamp}</dd>
              </div>
            )}

            <div>
              <dt className="font-medium text-muted-foreground">Relevance</dt>
              <dd className="mt-1 text-card-foreground">
                {(source.score * 100).toFixed(0)}%
              </dd>
            </div>
          </dl>
        </div>

        <div>
          <h3 className="text-sm font-semibold text-card-foreground">
            Source preview
          </h3>
          <div className="mt-3 whitespace-pre-wrap rounded-2xl bg-primary p-4 text-sm leading-6 text-primary-foreground">
            {source.text}
          </div>
        </div>

        <details className="rounded-2xl border border-border bg-background px-4 py-3 text-sm">
          <summary className="cursor-pointer font-medium text-muted-foreground">
            Technical reference
          </summary>
          <dl className="mt-3 grid gap-3 text-xs">
            <TechnicalItem label="Document ID" value={source.document_id} />
            <TechnicalItem label="Chunk ID" value={source.chunk_id} />
            <TechnicalItem label="Source ID" value={source.source_id} />
            {source.source_start_offset !== null && (
              <TechnicalItem
                label="Start offset"
                value={source.source_start_offset.toString()}
              />
            )}
            {source.source_end_offset !== null && (
              <TechnicalItem
                label="End offset"
                value={source.source_end_offset.toString()}
              />
            )}
          </dl>
        </details>
      </div>
    </aside>
  );
}

function buildSourceFacts(
  source: QuerySource,
): Array<{ label: string; value: string }> {
  const metadata = source.metadata;
  const facts: Array<{ label: string; value: string }> = [];

  addFact(facts, "Title", readString(metadata, "title"));
  addFact(facts, "Filename", readString(metadata, "filename"));

  const url = readString(metadata, "final_url") ?? readString(metadata, "url");
  addFact(facts, "URL", url);

  const timestamp = formatMetadataTimestamp(metadata);
  addFact(facts, "Timestamp", timestamp);

  const page = source.source_page ?? readNumber(metadata, "page_number");
  if (page !== null) addFact(facts, "Page", page.toString());

  const slide = readNumber(metadata, "slide_number");
  if (slide !== null) addFact(facts, "Slide", slide.toString());
  addFact(facts, "Slide title", readString(metadata, "slide_title"));

  const sheetName = readString(metadata, "sheet_name");
  const rowStart = readNumber(metadata, "row_start");
  const rowEnd = readNumber(metadata, "row_end");
  if (rowStart !== null && rowEnd !== null) {
    addFact(
      facts,
      "Rows",
      [sheetName ? `Sheet ${sheetName}` : null, `${rowStart}-${rowEnd}`]
        .filter(Boolean)
        .join(", "),
    );
  }

  const filePath = readString(metadata, "file_path");
  const lineStart = readNumber(metadata, "line_start");
  const lineEnd = readNumber(metadata, "line_end");
  addFact(facts, "File path", filePath);
  if (lineStart !== null && lineEnd !== null) {
    addFact(facts, "Lines", `${lineStart}-${lineEnd}`);
  }

  const lowConfidence = metadata?.low_confidence;
  if (lowConfidence === true) {
    addFact(facts, "OCR confidence", "Low - review recommended");
  }

  return facts;
}

function addFact(
  facts: Array<{ label: string; value: string }>,
  label: string,
  value: string | null,
) {
  if (value) {
    facts.push({ label, value });
  }
}

function readString(
  metadata: Record<string, unknown> | undefined,
  key: string,
): string | null {
  const value = metadata?.[key];
  return typeof value === "string" && value.trim() ? value : null;
}

function readRawString(
  metadata: Record<string, unknown> | undefined,
  key: string,
): string | null {
  const value = metadata?.[key];
  return typeof value === "string" && value.trim() ? value : null;
}

function readNumber(
  metadata: Record<string, unknown> | undefined,
  key: string,
): number | null {
  const value = metadata?.[key];
  return typeof value === "number" ? value : null;
}

function TechnicalItem({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <dt className="font-medium text-muted-foreground">{label}</dt>
      <dd className="mt-1 break-all font-mono text-muted-foreground">{value}</dd>
    </div>
  );
}
