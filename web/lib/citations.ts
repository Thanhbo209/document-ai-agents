/**
 * Citation display utilities.
 *
 * IMPORTANT: These helpers are display-only.
 * Backend citation data (source_id, chunk_id, etc.) is never mutated.
 * Only the visible text shown to users is transformed.
 */
import { humanizeSourceType } from "./format";

/**
 * Strips inline citation markers like [S1], [S2], [S12] from the
 * visible chat message text.
 *
 * The backend still returns these markers in the raw message string.
 * This helper removes them only for display purposes.
 */
export function stripCitationMarkers(message: string): string {
  return message.replace(/\s*\[S\d+\]/g, "").trim();
}

/**
 * Formats a source_id for user-facing display.
 *
 * The source_id from the backend looks like "S1", "S2", etc.
 * We display it as "Source 1", "Source 2" etc.
 *
 * Falls back gracefully for unexpected formats.
 */
export function formatCitationLabel(sourceId: string): string {
  // Match pattern like "S1", "S2", "S10"
  const match = /^S(\d+)$/i.exec(sourceId.trim());
  if (match) {
    return `Source ${match[1]}`;
  }
  // Fallback: just show "Source" + the raw id
  return `Source ${sourceId}`;
}

/**
 * Returns a short citation number from a source_id.
 * "S3" → 3, "S12" → 12
 */
export function citationNumber(sourceId: string): number | null {
  const match = /^S(\d+)$/i.exec(sourceId.trim());
  if (match) {
    return parseInt(match[1], 10);
  }
  return null;
}

export function formatMetadataTimestamp(
  metadata: Record<string, unknown> | undefined,
): string | null {
  const start = metadata?.timestamp_start;
  const end = metadata?.timestamp_end;

  if (typeof start !== "string" || !start) {
    return null;
  }

  if (typeof end === "string" && end && end !== start) {
    return `${start}-${end}`;
  }

  return start;
}

export function formatSourceMetadataSummary(
  metadata: Record<string, unknown> | undefined,
): string | null {
  const sourceType = readString(metadata, "source_type");

  if (sourceType === "web") {
    const title = readString(metadata, "title");
    const url = readString(metadata, "final_url") ?? readString(metadata, "url");
    return ["Web Page", title ?? url].filter(Boolean).join(" · ");
  }

  if (sourceType === "youtube") {
    const timestamp = formatMetadataTimestamp(metadata);
    return ["YouTube", timestamp].filter(Boolean).join(" · ");
  }

  if (sourceType === "repo") {
    const filePath = readString(metadata, "file_path");
    const lineStart = readNumber(metadata, "line_start");
    const lineEnd = readNumber(metadata, "line_end");
    const lineLabel =
      lineStart && lineEnd ? `Lines ${lineStart}-${lineEnd}` : null;
    return ["Repository", filePath, lineLabel].filter(Boolean).join(" · ");
  }

  return formatMetadataTimestamp(metadata);
}

export function formatSourceKind(
  metadata: Record<string, unknown> | undefined,
): string {
  const sourceType = readString(metadata, "source_type");
  return sourceType ? humanizeSourceType(sourceType) : "Source";
}

export function formatCitationDetail(
  metadata: Record<string, unknown> | undefined,
  sourcePage?: number | null,
): string | null {
  const timestamp = formatMetadataTimestamp(metadata);
  if (timestamp) return timestamp;

  const filePath = readString(metadata, "file_path");
  const lineStart = readNumber(metadata, "line_start");
  const lineEnd = readNumber(metadata, "line_end");
  if (filePath && lineStart && lineEnd) {
    return `${filePath} lines ${lineStart}-${lineEnd}`;
  }

  const sheetName = readString(metadata, "sheet_name");
  const rowStart = readNumber(metadata, "row_start");
  const rowEnd = readNumber(metadata, "row_end");
  if (rowStart && rowEnd) {
    return [sheetName ? `Sheet ${sheetName}` : null, `Rows ${rowStart}-${rowEnd}`]
      .filter(Boolean)
      .join(", ");
  }

  const slideNumber = readNumber(metadata, "slide_number");
  const slideTitle = readString(metadata, "slide_title");
  if (slideNumber) {
    return [`Slide ${slideNumber}`, slideTitle].filter(Boolean).join(" - ");
  }

  const pageNumber = sourcePage ?? readNumber(metadata, "page_number");
  if (pageNumber) return `Page ${pageNumber}`;

  const url = readString(metadata, "final_url") ?? readString(metadata, "url");
  return url;
}

function readString(
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
