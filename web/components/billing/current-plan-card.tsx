import type { BillingSummary } from "../../lib/api";
import { formatDate, formatBytes, humanizeStatus } from "../../lib/format";
import { SectionCard } from "../ui/section-card";
import { StatusBadge } from "../ui/status-badge";

type CurrentPlanCardProps = {
  summary: BillingSummary;
};

export function CurrentPlanCard({ summary }: CurrentPlanCardProps) {
  const { plan, subscription } = summary;
  const limits = plan.limits;

  const periodStart = subscription.current_period_start
    ? formatDate(subscription.current_period_start)
    : null;
  const periodEnd = subscription.current_period_end
    ? formatDate(subscription.current_period_end)
    : null;

  return (
    <SectionCard>
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <p className="text-sm font-medium text-muted-foreground">Current plan</p>
          <h2 className="mt-2 text-4xl font-semibold tracking-tight text-card-foreground">
            {plan.display_name}
          </h2>
          {plan.description && (
            <p className="mt-2 max-w-xl text-sm leading-6 text-muted-foreground">
              {plan.description}
            </p>
          )}
        </div>
        <StatusBadge status={subscription.status} />
      </div>

      {/* Plan limits in readable format */}
      <dl className="mt-6 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        <LimitItem label="Storage" value={formatBytes(limits.storage_bytes_limit)} />
        <LimitItem label="Documents" value={limits.documents_limit.toLocaleString()} />
        <LimitItem label="Daily queries" value={limits.daily_query_limit.toLocaleString()} />
        <LimitItem
          label="Monthly LLM tokens"
          value={limits.monthly_llm_token_limit.toLocaleString()}
        />
        <LimitItem
          label="Concurrent jobs"
          value={limits.concurrent_job_limit.toString()}
        />
        {periodEnd && (
          <LimitItem label="Period ends" value={periodEnd} />
        )}
      </dl>

      {/* Subscription period */}
      {(periodStart || periodEnd) && (
        <p className="mt-4 text-xs text-muted-foreground">
          Billing period: {periodStart ?? "—"} to {periodEnd ?? "—"} ·{" "}
          {humanizeStatus(subscription.status)}
        </p>
      )}
    </SectionCard>
  );
}

function LimitItem({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex flex-col gap-0.5">
      <dt className="text-xs text-muted-foreground">{label}</dt>
      <dd className="text-sm font-semibold tabular-nums text-card-foreground">
        {value}
      </dd>
    </div>
  );
}
