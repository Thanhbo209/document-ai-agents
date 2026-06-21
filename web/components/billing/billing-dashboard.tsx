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
    <main className="min-h-screen bg-slate-50 px-6 py-8">
      <div className="mx-auto max-w-6xl">
        <header className="mb-8">
          <p className="text-sm font-medium text-slate-500">
            Workspace billing
          </p>
          <h1 className="mt-2 text-3xl font-bold tracking-tight text-slate-950">
            Plans and limits
          </h1>
          <p className="mt-2 max-w-2xl text-slate-600">
            Internal plan switching only. Stripe is not connected yet.
          </p>
          <p className="mt-3 font-mono text-xs text-slate-400">
            {workspaceId}
          </p>
        </header>

        {errorMessage && (
          <p className="mb-6 rounded-lg bg-red-50 px-4 py-3 text-sm text-red-700">
            {errorMessage}
          </p>
        )}

        {isLoading ? (
          <div className="rounded-2xl border border-slate-200 bg-white p-10 text-center text-slate-500">
            Loading billing...
          </div>
        ) : (
          <div className="space-y-6">
            {summary && (
              <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
                <p className="text-sm font-medium text-slate-500">
                  Current plan
                </p>
                <div className="mt-3 flex flex-wrap items-end justify-between gap-4">
                  <div>
                    <h2 className="text-3xl font-bold text-slate-950">
                      {summary.plan.display_name}
                    </h2>
                    <p className="mt-1 text-sm text-slate-500">
                      Status: {summary.subscription.status}
                    </p>
                  </div>
                  <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-medium text-slate-700">
                    {summary.subscription.plan_name}
                  </span>
                </div>
              </section>
            )}

            <section className="grid gap-4 md:grid-cols-2">
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
              <h2 className="mb-4 text-xl font-semibold text-slate-950">
                Current usage
              </h2>
              <div className="grid gap-4 md:grid-cols-2">
                {metrics.map((metric) => (
                  <UsageMiniCard key={metric.metric_name} metric={metric} />
                ))}
              </div>
            </section>
          </div>
        )}
      </div>
    </main>
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
    <article className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h3 className="text-xl font-semibold text-slate-950">
            {plan.display_name}
          </h3>
          <p className="mt-2 text-sm text-slate-600">{plan.description}</p>
        </div>
        {isCurrent && (
          <span className="rounded-full bg-emerald-50 px-3 py-1 text-xs font-medium text-emerald-700">
            Current
          </span>
        )}
      </div>

      <dl className="mt-5 grid gap-2 text-sm text-slate-600">
        <LimitRow label="Storage" value={formatBytes(plan.limits.storage_bytes_limit)} />
        <LimitRow label="Documents" value={plan.limits.documents_limit.toLocaleString()} />
        <LimitRow label="Daily queries" value={plan.limits.daily_query_limit.toLocaleString()} />
        <LimitRow
          label="Monthly LLM tokens"
          value={plan.limits.monthly_llm_token_limit.toLocaleString()}
        />
        <LimitRow label="Concurrent jobs" value={plan.limits.concurrent_job_limit.toString()} />
      </dl>

      <button
        type="button"
        disabled={isCurrent || isChangingPlan}
        onClick={() => onChangePlan(plan.name)}
        className="mt-5 w-full rounded-lg bg-slate-950 px-4 py-2 text-sm font-medium text-white disabled:bg-slate-200 disabled:text-slate-500"
      >
        {isCurrent ? "Current plan" : `Switch to ${plan.display_name}`}
      </button>
    </article>
  );
}

function LimitRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between gap-4">
      <dt>{label}</dt>
      <dd className="font-medium text-slate-950">{value}</dd>
    </div>
  );
}

function UsageMiniCard({ metric }: { metric: UsageMetric }) {
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
          <p className="mt-2 text-2xl font-bold text-slate-950">
            {formatQuantity(metric.current, metric.unit)}
          </p>
        </div>
        {percentage !== null && (
          <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-medium text-slate-700">
            {percentage}%
          </span>
        )}
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
