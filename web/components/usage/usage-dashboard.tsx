"use client";

import { useEffect, useState } from "react";
import { getWorkspaceUsage, UsageMetric, UsagePlan } from "../../lib/usage-api";
import { DashboardShell } from "../layout/dashboard-shell";
import { Button } from "../ui/button";
import { EmptyState } from "../ui/empty-state";
import { ErrorState } from "../ui/error-state";
import { LoadingState } from "../ui/loading-state";
import { PageHeader } from "../ui/page-header";
import { StatCard } from "../ui/stat-card";
import { StatusBadge } from "../ui/status-badge";

type UsageDashboardProps = {
  workspaceId: string;
};

export function UsageDashboard({ workspaceId }: UsageDashboardProps) {
  const [plan, setPlan] = useState<UsagePlan | null>(null);
  const [metrics, setMetrics] = useState<UsageMetric[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  useEffect(() => {
    async function loadUsage() {
      setIsLoading(true);
      setErrorMessage(null);

      try {
        const response = await getWorkspaceUsage(workspaceId);
        setPlan(response.plan);
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

  const storageMetric = metrics.find(
    (metric) => metric.metric_name === "storage.bytes",
  );
  const queryMetric = metrics.find(
    (metric) => metric.metric_name === "query.count",
  );
  const documentMetric = metrics.find(
    (metric) => metric.metric_name === "document.count",
  );

  return (
    <DashboardShell
      activeItem="usage"
      title="Usage and limits"
      description="Track quota pressure across storage, documents, queries, chunks, and token usage."
      workspaceId={workspaceId}
    >
      <PageHeader
        kicker="Usage"
        title="Quota pressure without guesswork"
        description="Usage metrics roll up into the active plan so teams can see which limit matters before a request is blocked."
        meta={
          <p className="font-mono text-xs text-muted-foreground">{workspaceId}</p>
        }
        actions={
          <Button href={`/billing/${workspaceId}`} variant="secondary">
            View billing
          </Button>
        }
      />

      {errorMessage && (
        <div className="mb-6">
          <ErrorState message={errorMessage} />
        </div>
      )}

      {isLoading ? (
        <LoadingState title="Loading usage" />
      ) : (
        <div className="space-y-6">
          {plan && (
            <section className="rounded-3xl bg-card p-6 shadow-sm ring-1 ring-border/70">
              <div className="flex flex-wrap items-start justify-between gap-4">
                <div>
                  <p className="text-sm font-medium text-muted-foreground">
                    Current plan
                  </p>
                  <h2 className="mt-2 text-3xl font-semibold tracking-tight text-card-foreground">
                    {plan.display_name}
                  </h2>
                </div>
                <StatusBadge status={plan.status} />
              </div>
            </section>
          )}

          <section className="grid grid-flow-dense gap-4 md:grid-cols-3">
            <StatCard
              label="Storage"
              value={storageMetric ? formatQuantity(storageMetric.current, storageMetric.unit) : "-"}
              detail="Uploaded source bytes"
            />
            <StatCard
              label="Documents"
              value={documentMetric?.current ?? "-"}
              detail="Tracked document records"
            />
            <StatCard
              label="Queries"
              value={queryMetric?.current ?? "-"}
              detail="Questions asked today"
            />
          </section>

          {metrics.length === 0 ? (
            <EmptyState
              title="No usage recorded yet"
              description="Upload documents or run a query to start collecting usage metrics."
            />
          ) : (
            <section className="grid gap-4 md:grid-cols-2">
              {metrics.map((metric) => (
                <UsageCard key={metric.metric_name} metric={metric} />
              ))}
            </section>
          )}
        </div>
      )}
    </DashboardShell>
  );
}

function UsageCard({ metric }: { metric: UsageMetric }) {
  const percentage =
    metric.limit && metric.limit > 0
      ? Math.min(100, Math.round((metric.current / metric.limit) * 100))
      : null;

  return (
    <article className="rounded-3xl bg-card p-5 shadow-sm ring-1 ring-border/70">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-sm font-medium text-muted-foreground">
            {humanizeMetric(metric.metric_name)}
          </p>
          <p className="mt-2 font-mono text-3xl font-semibold tracking-tight text-card-foreground">
            {formatQuantity(metric.current, metric.unit)}
          </p>
        </div>

        {percentage !== null && <StatusBadge status={`${percentage}%`} />}
      </div>

      <p className="mt-3 text-sm text-muted-foreground">
        Limit:{" "}
        {metric.limit === null
          ? "Not limited"
          : formatQuantity(metric.limit, metric.unit)}
      </p>

      {percentage !== null && (
        <div className="mt-4 h-2 overflow-hidden rounded-full bg-muted">
          <div
            className="h-full rounded-full bg-primary transition-all duration-500"
            style={{ width: `${percentage}%` }}
          />
        </div>
      )}
    </article>
  );
}

function humanizeMetric(metricName: string): string {
  return metricName.replaceAll(".", " ");
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

  if (value < 1024 * 1024 * 1024) {
    return `${(value / (1024 * 1024)).toFixed(1)} MB`;
  }

  return `${(value / (1024 * 1024 * 1024)).toFixed(1)} GB`;
}
