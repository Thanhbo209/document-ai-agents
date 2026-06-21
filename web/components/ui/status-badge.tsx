import { humanizeStatus } from "../../lib/format";

type StatusBadgeProps = {
  status: string;
  /** If true, the raw status value is shown (for admin pages). Default: false (humanized) */
  raw?: boolean;
};

export function StatusBadge({ status, raw = false }: StatusBadgeProps) {
  const tone = toneForStatus(status);
  const label = raw ? status : humanizeStatus(status);

  return (
    <span
      className={[
        "inline-flex items-center rounded-lg px-2.5 py-1 text-xs font-medium ring-1",
        tone,
      ].join(" ")}
    >
      {label}
    </span>
  );
}

function toneForStatus(status: string): string {
  const lower = status.toLowerCase();

  if (lower.endsWith("failed") && !lower.startsWith("0 ")) {
    return "bg-red-50 text-red-700 ring-red-200 dark:bg-red-950/30 dark:text-red-400 dark:ring-red-800";
  }

  if (
    ["indexed", "succeeded", "approved", "active", "pro", "enterprise"].includes(lower)
  ) {
    return "bg-emerald-50 text-emerald-700 ring-emerald-200 dark:bg-emerald-950/30 dark:text-emerald-400 dark:ring-emerald-800";
  }

  if (["failed", "rejected", "error", "exceeded"].includes(lower)) {
    return "bg-red-50 text-red-700 ring-red-200 dark:bg-red-950/30 dark:text-red-400 dark:ring-red-800";
  }

  if (["processing", "pending", "queued", "uploading"].includes(lower)) {
    return "bg-amber-50 text-amber-700 ring-amber-200 dark:bg-amber-950/30 dark:text-amber-400 dark:ring-amber-800";
  }

  if (lower === "pending_deletion") {
    return "bg-orange-50 text-orange-700 ring-orange-200 dark:bg-orange-950/30 dark:text-orange-400 dark:ring-orange-800";
  }

  return "bg-muted text-muted-foreground ring-border";
}
