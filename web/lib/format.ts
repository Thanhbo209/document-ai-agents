/**
 * Shared formatting utilities for human-readable display.
 * All transforms are display-only — backend values are never mutated.
 */

/**
 * Converts snake_case, dot.separated, and kebab-case identifiers to
 * Title Case human-readable labels.
 *
 * Examples:
 *   llm.tokens.monthly  → LLM Tokens Monthly
 *   query.count.daily   → Query Count Daily
 *   pending_deletion    → Pending Deletion
 *   source_type         → Source Type
 */
export function humanizeLabel(value: string): string {
  return value
    .replaceAll("_", " ")
    .replaceAll(".", " ")
    .replaceAll("-", " ")
    .replace(/\s+/g, " ")
    .trim()
    .replace(/\b\w/g, (char) => char.toUpperCase());
}

/**
 * Maps known metric names to user-friendly labels.
 * Falls back to humanizeLabel for unknown metrics.
 */
export function humanizeMetricName(metricName: string): string {
  const known: Record<string, string> = {
    "storage.bytes": "Storage Used",
    "document.count": "Documents",
    "query.count": "Queries Used",
    "query.count.daily": "Daily Queries",
    "llm.tokens.monthly": "LLM Tokens This Month",
    "chunk.tokens.monthly": "Chunk Tokens This Month",
    "embedding.tokens.monthly": "Embedding Tokens This Month",
    "chunk.count": "Indexed Chunks",
    "job.count": "Ingestion Jobs",
  };
  return known[metricName] ?? humanizeLabel(metricName);
}

/**
 * Maps known status values to human-readable Title Case.
 */
export function humanizeStatus(status: string): string {
  const known: Record<string, string> = {
    active: "Active",
    inactive: "Inactive",
    indexed: "Indexed",
    processing: "Processing",
    pending: "Pending",
    pending_deletion: "Pending Deletion",
    created: "Created",
    completed: "Completed",
    cancelled: "Cancelled",
    failed: "Failed",
    succeeded: "Succeeded",
    queued: "Queued",
    approved: "Approved",
    rejected: "Rejected",
    error: "Error",
    free: "Free",
    pro: "Pro",
    enterprise: "Enterprise",
  };
  return known[status] ?? humanizeLabel(status);
}

/**
 * Maps known source type values to readable labels.
 */
export function humanizeSourceType(sourceType: string): string {
  const known: Record<string, string> = {
    upload: "Uploaded File",
    pdf: "PDF Document",
    txt: "Text File",
    md: "Markdown File",
    markdown: "Markdown File",
    docx: "Word Document",
    pptx: "PowerPoint Deck",
    csv: "CSV Table",
    xlsx: "Excel Workbook",
    image: "OCR Image",
    png: "PNG Image",
    jpg: "JPEG Image",
    jpeg: "JPEG Image",
    tif: "TIFF Image",
    tiff: "TIFF Image",
    bmp: "Bitmap Image",
    audio: "Audio Transcript",
    video: "Video Transcript",
    mp3: "MP3 Audio",
    wav: "WAV Audio",
    m4a: "M4A Audio",
    flac: "FLAC Audio",
    ogg: "OGG Audio",
    mp4: "MP4 Video",
    mov: "MOV Video",
    mkv: "MKV Video",
    webm: "WebM Video",
    repo: "Repository ZIP",
    zip: "Repository ZIP",
    web: "Web Page",
    youtube: "YouTube Transcript",
    url: "Web URL",
    api: "API",
  };
  return known[sourceType] ?? humanizeLabel(sourceType);
}

/**
 * Formats a byte count into a readable storage string.
 */
export function formatBytes(value: number): string {
  if (value < 1024) {
    return `${value} B`;
  }
  if (value < 1024 * 1024) {
    return `${(value / 1024).toFixed(1)} KB`;
  }
  if (value < 1024 * 1024 * 1024) {
    return `${(value / (1024 * 1024)).toFixed(1)} MB`;
  }
  return `${(value / (1024 * 1024 * 1024)).toFixed(1)} GB`;
}

/**
 * Formats a metric value + unit into a readable string.
 */
export function formatQuantity(value: number, unit: string): string {
  if (unit === "bytes") {
    return formatBytes(value);
  }
  return `${value.toLocaleString()} ${unit}`;
}

/**
 * Formats a quantity with its limit for display.
 * e.g. "200 / 500,000 tokens used"
 */
export function formatUsageLabel(
  current: number,
  limit: number | null,
  unit: string,
): string {
  const currentStr = formatQuantity(current, unit);
  if (limit === null || limit <= 0) {
    return `${currentStr} (no limit)`;
  }
  const limitStr = formatQuantity(limit, unit);
  return `${currentStr} / ${limitStr}`;
}

/**
 * Formats an ISO date string to a short human-readable date.
 */
export function formatDate(isoString: string): string {
  try {
    return new Date(isoString).toLocaleDateString(undefined, {
      year: "numeric",
      month: "short",
      day: "numeric",
    });
  } catch {
    return "—";
  }
}

/**
 * Formats an ISO date string to a short relative-time description.
 */
export function formatRelativeTime(isoString: string): string {
  try {
    const date = new Date(isoString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
    const diffMins = Math.floor(diffMs / (1000 * 60));

    if (diffMins < 1) return "just now";
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    return formatDate(isoString);
  } catch {
    return "—";
  }
}

/**
 * Masks a raw ID for safe display on user-facing pages.
 * Shows only the last 4 characters prefixed with bullets.
 *
 * Example: "b658e6f2-..." → "•••• E6F2"
 */
export function maskId(id: string): string {
  const clean = id.replace(/-/g, "").toUpperCase();
  const suffix = clean.slice(-4);
  return `•••• ${suffix}`;
}

/**
 * Calculates usage percentage, capped at 100.
 */
export function usagePercent(current: number, limit: number | null): number | null {
  if (!limit || limit <= 0) return null;
  return Math.min(100, Math.round((current / limit) * 100));
}

/**
 * Returns a usage tone based on percentage.
 */
export type UsageTone = "healthy" | "warning" | "danger" | "exceeded";

export function usageTone(pct: number | null): UsageTone {
  if (pct === null) return "healthy";
  if (pct >= 100) return "exceeded";
  if (pct >= 85) return "danger";
  if (pct >= 65) return "warning";
  return "healthy";
}
