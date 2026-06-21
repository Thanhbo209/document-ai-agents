import type { BillingPlan } from "../../lib/api";
import { PlanCard } from "./plan-card";
import { SectionCard } from "../ui/section-card";

type PlanComparisonProps = {
  plans: BillingPlan[];
  currentPlanName?: string;
  isChangingPlan: boolean;
  onChangePlan: (planName: string) => void;
};

export function PlanComparison({
  plans,
  currentPlanName,
  isChangingPlan,
  onChangePlan,
}: PlanComparisonProps) {
  return (
    <div className="space-y-4">
      {/* Internal billing notice */}
      <SectionCard className="border-amber-200 bg-amber-50/60 ring-amber-200/60 dark:border-amber-800 dark:bg-amber-950/20 dark:ring-amber-800/40">
        <div className="flex items-start gap-3">
          <svg
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.8"
            strokeLinecap="round"
            strokeLinejoin="round"
            className="mt-0.5 h-5 w-5 shrink-0 text-amber-600 dark:text-amber-400"
            aria-hidden="true"
          >
            <path d="M12 9v4" />
            <path d="M12 17h.01" />
            <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0Z" />
          </svg>
          <div>
            <p className="text-sm font-semibold text-amber-800 dark:text-amber-300">
              Internal plan switching only
            </p>
            <p className="mt-1 text-sm text-amber-700 dark:text-amber-400">
              Stripe is not connected yet. Plan changes take effect immediately
              and are enforced internally. No payment is processed.
            </p>
          </div>
        </div>
      </SectionCard>

      {/* Plan cards grid */}
      <section
        className="grid grid-flow-dense gap-4 lg:grid-cols-2"
        aria-label="Available plans"
      >
        {plans.map((plan) => (
          <PlanCard
            key={plan.name}
            plan={plan}
            currentPlanName={currentPlanName}
            isChangingPlan={isChangingPlan}
            onChangePlan={onChangePlan}
          />
        ))}
      </section>
    </div>
  );
}
