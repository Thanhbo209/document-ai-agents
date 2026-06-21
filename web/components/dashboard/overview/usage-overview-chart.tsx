import {
  humanizeMetricName,
  formatQuantity,
  usagePercent,
  usageTone,
} from "../../../lib/format";
import { ProgressBar } from "../../ui/progress-bar";
import { SectionCard } from "../../ui/section-card";
import type { UsageMetric } from "../../../lib/usage-api";

type UsageOverviewChartProps = {
  metrics: UsageMetric[];
};

const PRIORITY_METRICS = [
  "storage.bytes",
  "query.count",
  "query.count.daily",
  "llm.tokens.monthly",
  "document.count",
  "chunk.tokens.monthly",
];

export function UsageOverviewChart({ metrics }: UsageOverviewChartProps) {
  // Show priority metrics first, then others
  const sorted = [...metrics].sort((a, b) => {
    const ai = PRIORITY_METRICS.indexOf(a.metric_name);
    const bi = PRIORITY_METRICS.indexOf(b.metric_name);
    if (ai === -1 && bi === -1) return 0;
    if (ai === -1) return 1;
    if (bi === -1) return -1;
    return ai - bi;
  });

  const displayed = sorted.slice(0, 6);

  if (displayed.length === 0) {
    return null;
  }

  return (
    <SectionCard>
      <p className="text-sm font-medium text-muted-foreground">Usage summary</p>
      <h3 className="mt-1 text-xl font-semibold tracking-tight text-card-foreground">
        Quota at a glance
      </h3>

      <div className="mt-6 grid gap-5 sm:grid-cols-2">
        {displayed.map((metric) => {
          const pct = usagePercent(metric.current, metric.limit);
          const tone = usageTone(pct);
          const label = humanizeMetricName(metric.metric_name);
          const currentStr = formatQuantity(metric.current, metric.unit);
          const limitStr =
            metric.limit !== null
              ? formatQuantity(metric.limit, metric.unit)
              : null;

          return (
            <div key={metric.metric_name} className="space-y-2">
              <div className="flex items-center justify-between gap-2">
                <span className="text-sm font-medium text-card-foreground">
                  {label}
                </span>
                {pct !== null && (
                  <span
                    className={`text-xs font-semibold tabular-nums ${toneTextClass(tone)}`}
                  >
                    {pct}%
                  </span>
                )}
              </div>
              {metric.limit !== null && metric.limit > 0 ? (
                <ProgressBar
                  value={metric.current}
                  max={metric.limit}
                  tone={tone}
                />
              ) : (
                <div className="h-2 overflow-hidden rounded-full bg-muted">
                  <div className="h-full w-full rounded-full bg-muted-foreground/20" />
                </div>
              )}
              <p className="text-xs text-muted-foreground">
                {currentStr}
                {limitStr ? ` / ${limitStr}` : " (no limit)"}
              </p>
            </div>
          );
        })}
      </div>
    </SectionCard>
  );
}

function toneTextClass(tone: ReturnType<typeof usageTone>): string {
  switch (tone) {
    case "healthy":
      return "text-emerald-600";
    case "warning":
      return "text-amber-600";
    case "danger":
      return "text-orange-600";
    case "exceeded":
      return "text-destructive";
  }
}
