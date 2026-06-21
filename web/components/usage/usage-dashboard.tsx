"use client";

import { useEffect, useState } from "react";
import { getWorkspaceUsage, UsageMetric } from "../../lib/usage-api";

type UsageDashboardProps = {
  workspaceId: string;
};

export function UsageDashboard({ workspaceId }: UsageDashboardProps) {
  const [metrics, setMetrics] = useState<UsageMetric[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  useEffect(() => {
    async function loadUsage() {
      setIsLoading(true);
      setErrorMessage(null);

      try {
        const response = await getWorkspaceUsage(workspaceId);
        setMetrics(response.metrics);
      } catch (error) {
        setErrorMessage(
          error instanceof Error ? error.message : "Could not load usage.",
        );
      } finally {
        setIsLoading(false);
      }
    }

    void loadUsage();
  }, [workspaceId]);

  return (
    <main className="min-h-screen bg-slate-50 px-6 py-8">
      <div className="mx-auto max-w-6xl">
        <header className="mb-8">
          <p className="text-sm font-medium text-slate-500">Workspace usage</p>
          <h1 className="mt-2 text-3xl font-bold tracking-tight text-slate-950">
            Quotas and cost controls
          </h1>
          <p className="mt-2 max-w-2xl text-slate-600">
            Track storage, documents, queries, chunks, and answer token usage.
          </p>
          <p className="mt-3 font-mono text-xs text-slate-400">{workspaceId}</p>
        </header>

        {errorMessage && (
          <p className="mb-6 rounded-lg bg-red-50 px-4 py-3 text-sm text-red-700">
            {errorMessage}
          </p>
        )}

        {isLoading ? (
          <div className="rounded-2xl border border-slate-200 bg-white p-10 text-center text-slate-500">
            Loading usage...
          </div>
        ) : (
          <section className="grid gap-4 md:grid-cols-2">
            {metrics.map((metric) => (
              <UsageCard key={metric.metric_name} metric={metric} />
            ))}
          </section>
        )}
      </div>
    </main>
  );
}

function UsageCard({ metric }: { metric: UsageMetric }) {
  const percentage =
    metric.limit && metric.limit > 0
      ? Math.min(100, Math.round((metric.current / metric.limit) * 100))
      : null;

  return (
    <article className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-sm font-medium text-slate-500">
            {metric.metric_name}
          </p>
          <p className="mt-2 text-3xl font-bold text-slate-950">
            {formatQuantity(metric.current, metric.unit)}
          </p>
        </div>

        {percentage !== null && (
          <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-medium text-slate-700">
            {percentage}%
          </span>
        )}
      </div>

      <p className="mt-3 text-sm text-slate-500">
        Limit:{" "}
        {metric.limit === null
          ? "Not limited"
          : formatQuantity(metric.limit, metric.unit)}
      </p>

      {percentage !== null && (
        <div className="mt-4 h-2 overflow-hidden rounded-full bg-slate-100">
          <div
            className="h-full rounded-full bg-slate-950"
            style={{ width: `${percentage}%` }}
          />
        </div>
      )}
    </article>
  );
}

function formatQuantity(value: number, unit: string): string {
  if (unit === "bytes") {
    return formatBytes(value);
  }

  return `${value.toLocaleString()} ${unit}`;
}

function formatBytes(value: number): string {
  if (value < 1024) {
    return `${value} B`;
  }

  if (value < 1024 * 1024) {
    return `${(value / 1024).toFixed(1)} KB`;
  }

  return `${(value / (1024 * 1024)).toFixed(1)} MB`;
}
