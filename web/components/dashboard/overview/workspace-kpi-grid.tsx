import { StatCard } from "../../ui/stat-card";
import { formatBytes } from "../../../lib/format";
import type { UsageMetric } from "../../../lib/usage-api";
import type { WorkspaceDocument } from "../../../lib/upload-api";

type WorkspaceKpiGridProps = {
  documents: WorkspaceDocument[];
  metrics: UsageMetric[];
  planDisplayName: string;
};

export function WorkspaceKpiGrid({
  documents,
  metrics,
  planDisplayName,
}: WorkspaceKpiGridProps) {
  const total = documents.length;
  const indexed = documents.filter((d) => d.status === "indexed").length;
  const failed = documents.filter((d) => d.status === "failed").length;

  const storageMetric = metrics.find((m) => m.metric_name === "storage.bytes");
  const queryMetric = metrics.find(
    (m) =>
      m.metric_name === "query.count" ||
      m.metric_name === "query.count.daily",
  );

  return (
    <section
      className="grid grid-flow-dense gap-4 sm:grid-cols-2 xl:grid-cols-4"
      aria-label="Workspace KPIs"
    >
      <StatCard
        label="Documents"
        value={total}
        detail={indexed > 0 ? `${indexed} indexed` : "None indexed yet"}
        tone={indexed === total && total > 0 ? "good" : "neutral"}
        icon={
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" className="h-4 w-4" aria-hidden="true">
            <path d="M7 3.5h7l3 3V20a1 1 0 0 1-1 1H7a1 1 0 0 1-1-1V4.5a1 1 0 0 1 1-1Z" />
            <path d="M14 3.5V7h3" />
          </svg>
        }
      />

      <StatCard
        label="Storage used"
        value={
          storageMetric ? formatBytes(storageMetric.current) : "—"
        }
        detail={
          storageMetric?.limit
            ? `of ${formatBytes(storageMetric.limit)} limit`
            : "No storage limit"
        }
        tone="neutral"
        icon={
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" className="h-4 w-4" aria-hidden="true">
            <ellipse cx="12" cy="7" rx="8" ry="3.5" />
            <path d="M4 7v10c0 1.93 3.58 3.5 8 3.5s8-1.57 8-3.5V7" />
          </svg>
        }
      />

      <StatCard
        label="Queries used"
        value={queryMetric?.current ?? "—"}
        detail="Questions asked today"
        tone="neutral"
        icon={
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" className="h-4 w-4" aria-hidden="true">
            <path d="M5 6.5A3.5 3.5 0 0 1 8.5 3h7A3.5 3.5 0 0 1 19 6.5v4A3.5 3.5 0 0 1 15.5 14H11l-4.5 4v-4.5A3.5 3.5 0 0 1 5 10.5v-4Z" />
          </svg>
        }
      />

      <StatCard
        label="Current plan"
        value={planDisplayName}
        detail={failed > 0 ? `${failed} failed ${failed === 1 ? "document" : "documents"}` : "All documents healthy"}
        tone={failed > 0 ? "warning" : "good"}
        icon={
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" className="h-4 w-4" aria-hidden="true">
            <path d="M5 7.5A2.5 2.5 0 0 1 7.5 5h9A2.5 2.5 0 0 1 19 7.5v9A2.5 2.5 0 0 1 16.5 19h-9A2.5 2.5 0 0 1 5 16.5v-9Z" />
            <path d="M5 9h14" />
          </svg>
        }
      />
    </section>
  );
}
