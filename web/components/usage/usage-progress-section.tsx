import type { UsageMetric } from "../../lib/usage-api";
import { UsageMetricCard } from "./usage-metric-card";
import { EmptyState } from "../ui/empty-state";

type UsageProgressSectionProps = {
  metrics: UsageMetric[];
};

export function UsageProgressSection({ metrics }: UsageProgressSectionProps) {
  if (metrics.length === 0) {
    return (
      <EmptyState
        title="No usage recorded yet"
        description="Upload documents or run a query to start collecting usage metrics."
        icon={
          <svg
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.6"
            strokeLinecap="round"
            strokeLinejoin="round"
            className="h-7 w-7"
            aria-hidden="true"
          >
            <path d="M4 19V5" />
            <path d="M4 19h16" />
            <path d="M8 16v-5" />
            <path d="M12 16V8" />
            <path d="M16 16v-3" />
          </svg>
        }
      />
    );
  }

  return (
    <div className="grid gap-4 md:grid-cols-2">
      {metrics.map((metric) => (
        <UsageMetricCard key={metric.metric_name} metric={metric} />
      ))}
    </div>
  );
}
