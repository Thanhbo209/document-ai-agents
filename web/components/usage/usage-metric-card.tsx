import {
  humanizeMetricName,
  formatQuantity,
  usagePercent,
  usageTone,
  type UsageTone,
} from "../../lib/format";
import { ProgressBar } from "../ui/progress-bar";
import type { UsageMetric } from "../../lib/usage-api";

type UsageMetricCardProps = {
  metric: UsageMetric;
};

const STATUS_LABELS: Record<UsageTone, string> = {
  healthy: "Healthy",
  warning: "Approaching limit",
  danger: "Near limit",
  exceeded: "Limit reached",
};

const STATUS_BADGE_CLASSES: Record<UsageTone, string> = {
  healthy:
    "bg-emerald-50 text-emerald-700 ring-emerald-200 dark:bg-emerald-950/30 dark:text-emerald-400 dark:ring-emerald-800",
  warning:
    "bg-amber-50 text-amber-700 ring-amber-200 dark:bg-amber-950/30 dark:text-amber-400 dark:ring-amber-800",
  danger:
    "bg-orange-50 text-orange-700 ring-orange-200 dark:bg-orange-950/30 dark:text-orange-400 dark:ring-orange-800",
  exceeded:
    "bg-red-50 text-red-700 ring-red-200 dark:bg-red-950/30 dark:text-red-400 dark:ring-red-800",
};

export function UsageMetricCard({ metric }: UsageMetricCardProps) {
  const pct = usagePercent(metric.current, metric.limit);
  const tone = usageTone(pct);
  const label = humanizeMetricName(metric.metric_name);
  const currentStr = formatQuantity(metric.current, metric.unit);
  const limitStr =
    metric.limit !== null ? formatQuantity(metric.limit, metric.unit) : null;

  return (
    <article className="rounded-3xl bg-card p-5 shadow-sm ring-1 ring-border/70 transition duration-200 hover:-translate-y-0.5 hover:shadow-md">
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0 flex-1">
          <p className="text-sm font-medium text-muted-foreground">{label}</p>
          <p className="mt-2 font-mono text-3xl font-semibold tracking-tight tabular-nums text-card-foreground">
            {currentStr}
          </p>
        </div>

        {pct !== null && (
          <span
            className={`inline-flex items-center rounded-lg px-2.5 py-1 text-xs font-medium ring-1 ${STATUS_BADGE_CLASSES[tone]}`}
          >
            {STATUS_LABELS[tone]}
          </span>
        )}
      </div>

      {limitStr && (
        <p className="mt-2 text-sm text-muted-foreground">
          Limit: {limitStr}
        </p>
      )}

      {metric.limit !== null && metric.limit > 0 && (
        <ProgressBar
          value={metric.current}
          max={metric.limit}
          tone={tone}
          showLabel
          className="mt-4"
        />
      )}

      {metric.limit === null && (
        <p className="mt-3 text-xs text-muted-foreground">No limit on this plan</p>
      )}
    </article>
  );
}
