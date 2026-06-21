/**
 * Citation display utilities.
 *
 * IMPORTANT: These helpers are display-only.
 * Backend citation data (source_id, chunk_id, etc.) is never mutated.
 * Only the visible text shown to users is transformed.
 */

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
