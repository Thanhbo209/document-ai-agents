"use client";

import { useCallback, useEffect, useState } from "react";
import {
  BillingPlan,
  BillingSummary,
  changeWorkspacePlan,
  getBillingSummary,
  listBillingPlans,
} from "../../lib/api";
import { getWorkspaceUsage, UsageMetric } from "../../lib/usage-api";
import { DashboardShell } from "../layout/dashboard-shell";
import { Button } from "../ui/button";
import { EmptyState } from "../ui/empty-state";
import { ErrorState } from "../ui/error-state";
import { LoadingState } from "../ui/loading-state";
import { PageHeader } from "../ui/page-header";
import { StatusBadge } from "../ui/status-badge";

type BillingDashboardProps = {
  workspaceId: string;
};

export function BillingDashboard({ workspaceId }: BillingDashboardProps) {
  const [summary, setSummary] = useState<BillingSummary | null>(null);
  const [plans, setPlans] = useState<BillingPlan[]>([]);
  const [metrics, setMetrics] = useState<UsageMetric[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isChangingPlan, setIsChangingPlan] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    setIsLoading(true);
    setErrorMessage(null);

    try {
      const [billingSummary, availablePlans, usageSummary] = await Promise.all([
        getBillingSummary(workspaceId),
        listBillingPlans(workspaceId),
        getWorkspaceUsage(workspaceId),
      ]);

      setSummary(billingSummary);
      setPlans(availablePlans);
      setMetrics(usageSummary.metrics);
    } catch (error) {
      setErrorMessage(
        error instanceof Error ? error.message : "Could not load billing.",
      );
    } finally {
      setIsLoading(false);
    }
  }, [workspaceId]);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    void refresh();
  }, [refresh]);

  async function changePlan(planName: string) {
    setIsChangingPlan(true);
    setErrorMessage(null);

    try {
      const updatedSummary = await changeWorkspacePlan(workspaceId, planName);
      setSummary(updatedSummary);
      await refresh();
    } catch (error) {
      setErrorMessage(
        error instanceof Error ? error.message : "Could not change plan.",
      );
    } finally {
      setIsChangingPlan(false);
    }
  }

  return (
    <DashboardShell
      activeItem="billing"
      title="Billing and plans"
      description="Inspect internal plan limits and switch workspace plans without Stripe."
      workspaceId={workspaceId}
    >
      <PageHeader
        kicker="Billing"
        title="Internal plan controls"
        description="Plan switching is internal only. Stripe is not connected yet, but limits still drive quota enforcement."
        meta={
          <p className="font-mono text-xs text-muted-foreground">{workspaceId}</p>
        }
        actions={
          <Button href={`/usage/${workspaceId}`} variant="secondary">
            View usage
          </Button>
        }
      />

      {errorMessage && (
        <div className="mb-6">
          <ErrorState message={errorMessage} />
        </div>
      )}

      {isLoading ? (
        <LoadingState title="Loading billing" />
      ) : (
        <div className="space-y-6">
          {summary && (
            <section className="rounded-3xl bg-card p-6 shadow-sm ring-1 ring-border/70">
              <div className="flex flex-wrap items-end justify-between gap-4">
                <div>
                  <p className="text-sm font-medium text-muted-foreground">
                    Current plan
                  </p>
                  <h2 className="mt-2 text-4xl font-semibold tracking-tight text-card-foreground">
                    {summary.plan.display_name}
                  </h2>
                  <p className="mt-2 text-sm text-muted-foreground">
                    Subscription status: {summary.subscription.status}
                  </p>
                </div>
                <StatusBadge status={summary.subscription.plan_name} />
              </div>
            </section>
          )}

          <section className="grid grid-flow-dense gap-4 lg:grid-cols-2">
            {plans.map((plan) => (
              <PlanCard
                key={plan.name}
                plan={plan}
                currentPlanName={summary?.subscription.plan_name}
                isChangingPlan={isChangingPlan}
                onChangePlan={(planName) => void changePlan(planName)}
              />
            ))}
          </section>

          <section>
            <h2 className="mb-4 text-xl font-semibold tracking-tight text-foreground">
              Current usage
            </h2>
            {metrics.length === 0 ? (
              <EmptyState
                title="No usage recorded"
                description="Usage appears here after uploads, queries, and indexing activity."
              />
            ) : (
              <div className="grid gap-4 md:grid-cols-2">
                {metrics.map((metric) => (
                  <UsageMiniCard key={metric.metric_name} metric={metric} />
                ))}
              </div>
            )}
          </section>
        </div>
      )}
    </DashboardShell>
  );
}

function PlanCard({
  plan,
  currentPlanName,
  isChangingPlan,
  onChangePlan,
}: {
  plan: BillingPlan;
  currentPlanName?: string;
  isChangingPlan: boolean;
  onChangePlan: (planName: string) => void;
}) {
  const isCurrent = plan.name === currentPlanName;

  return (
    <article
      className={[
        "flex min-h-full flex-col rounded-3xl bg-card p-6 shadow-sm ring-1 transition duration-200 hover:-translate-y-1 hover:shadow-md",
        isCurrent ? "ring-primary/40" : "ring-border/70",
      ].join(" ")}
    >
      <div className="flex items-start justify-between gap-4">
        <div>
          <h3 className="text-2xl font-semibold tracking-tight text-card-foreground">
            {plan.display_name}
          </h3>
          <p className="mt-2 text-sm leading-6 text-muted-foreground">
            {plan.description}
          </p>
        </div>
        {isCurrent && <StatusBadge status="active" />}
      </div>

      <dl className="mt-6 grid gap-3 text-sm text-muted-foreground">
        <LimitRow
          label="Storage"
          value={formatBytes(plan.limits.storage_bytes_limit)}
        />
        <LimitRow
          label="Documents"
          value={plan.limits.documents_limit.toLocaleString()}
        />
        <LimitRow
          label="Daily queries"
          value={plan.limits.daily_query_limit.toLocaleString()}
        />
        <LimitRow
          label="Monthly LLM tokens"
          value={plan.limits.monthly_llm_token_limit.toLocaleString()}
        />
        <LimitRow
          label="Concurrent jobs"
          value={plan.limits.concurrent_job_limit.toString()}
        />
      </dl>

      <Button
        disabled={isCurrent || isChangingPlan}
        onClick={() => onChangePlan(plan.name)}
        className="mt-6 w-full"
        variant={isCurrent ? "secondary" : "primary"}
      >
        {isCurrent ? "Current plan" : `Switch to ${plan.display_name}`}
      </Button>
    </article>
  );
}

function LimitRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between gap-4 border-b border-border/60 pb-2 last:border-0">
      <dt>{label}</dt>
      <dd className="font-mono font-medium text-card-foreground">{value}</dd>
    </div>
  );
}

function UsageMiniCard({ metric }: { metric: UsageMetric }) {
  const percentage =
    metric.limit && metric.limit > 0
      ? Math.min(100, Math.round((metric.current / metric.limit) * 100))
      : null;

  return (
    <article className="rounded-3xl bg-card p-5 shadow-sm ring-1 ring-border/70">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-sm font-medium text-muted-foreground">
            {metric.metric_name.replaceAll(".", " ")}
          </p>
          <p className="mt-2 font-mono text-2xl font-semibold tracking-tight text-card-foreground">
            {formatQuantity(metric.current, metric.unit)}
          </p>
        </div>
        {percentage !== null && <StatusBadge status={`${percentage}%`} />}
      </div>
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

  if (value < 1024 * 1024 * 1024) {
    return `${(value / (1024 * 1024)).toFixed(1)} MB`;
  }

  return `${(value / (1024 * 1024 * 1024)).toFixed(1)} GB`;
}
