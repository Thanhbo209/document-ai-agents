import type { BillingPlan } from "../../lib/api";
import { formatBytes } from "../../lib/format";
import { Button } from "../ui/button";

type PlanCardProps = {
  plan: BillingPlan;
  currentPlanName?: string;
  isChangingPlan: boolean;
  onChangePlan: (planName: string) => void;
};

export function PlanCard({
  plan,
  currentPlanName,
  isChangingPlan,
  onChangePlan,
}: PlanCardProps) {
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
          {plan.description && (
            <p className="mt-2 text-sm leading-6 text-muted-foreground">
              {plan.description}
            </p>
          )}
        </div>
        {isCurrent && (
          <span className="inline-flex items-center rounded-lg bg-primary/10 px-2.5 py-1 text-xs font-medium text-primary ring-1 ring-primary/20">
            Current
          </span>
        )}
      </div>

      <dl className="mt-6 flex-1 space-y-3 text-sm text-muted-foreground">
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
    <div className="flex justify-between gap-4 border-b border-border/60 pb-2.5 last:border-0">
      <dt>{label}</dt>
      <dd className="font-mono font-semibold tabular-nums text-card-foreground">
        {value}
      </dd>
    </div>
  );
}
