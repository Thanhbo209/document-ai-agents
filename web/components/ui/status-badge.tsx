type StatusBadgeProps = {
  status: string;
};

export function StatusBadge({ status }: StatusBadgeProps) {
  const tone = toneForStatus(status);

  return (
    <span
      className={[
        "inline-flex items-center rounded-lg px-2.5 py-1 text-xs font-medium ring-1",
        tone,
      ].join(" ")}
    >
      {status}
    </span>
  );
}

function toneForStatus(status: string): string {
  if (status.endsWith("failed") && !status.startsWith("0 ")) {
    return "bg-red-50 text-red-700 ring-red-200";
  }

  if (["indexed", "succeeded", "approved", "active", "pro"].includes(status)) {
    return "bg-emerald-50 text-emerald-700 ring-emerald-200";
  }

  if (["failed", "rejected", "error"].includes(status)) {
    return "bg-red-50 text-red-700 ring-red-200";
  }

  if (["processing", "pending", "queued"].includes(status)) {
    return "bg-amber-50 text-amber-700 ring-amber-200";
  }

  return "bg-muted text-muted-foreground ring-border";
}
