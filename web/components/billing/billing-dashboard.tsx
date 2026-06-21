"use client";

import { useCallback, useEffect, useState } from "react";
import {
  BillingPlan,
  BillingSummary,
  changeWorkspacePlan,
  getBillingSummary,
  listBillingPlans,
} from "../../lib/api";
import { DashboardShell } from "../layout/dashboard-shell";
import { Button } from "../ui/button";
import { ErrorState } from "../ui/error-state";
import { LoadingState } from "../ui/loading-state";
import { PageHeader } from "../ui/page-header";
import { CurrentPlanCard } from "./current-plan-card";
import { PlanComparison } from "./plan-comparison";

type BillingDashboardProps = {
  workspaceId: string;
};

export function BillingDashboard({ workspaceId }: BillingDashboardProps) {
  const [summary, setSummary] = useState<BillingSummary | null>(null);
  const [plans, setPlans] = useState<BillingPlan[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isChangingPlan, setIsChangingPlan] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    setIsLoading(true);
    setErrorMessage(null);

    try {
      const [billingSummary, availablePlans] = await Promise.all([
        getBillingSummary(workspaceId),
        listBillingPlans(workspaceId),
      ]);

      setSummary(billingSummary);
      setPlans(availablePlans);
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
    setSuccessMessage(null);

    try {
      const updatedSummary = await changeWorkspacePlan(workspaceId, planName);
      setSummary(updatedSummary);
      const newPlan = plans.find((p) => p.name === planName);
      setSuccessMessage(
        `Plan changed to ${newPlan?.display_name ?? planName}.`,
      );
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
      title="Billing"
      description="View your current plan limits and switch plans."
      workspaceId={workspaceId}
    >
      <PageHeader
        kicker="Plan management"
        title="Your workspace plan"
        description="Plan limits drive quota enforcement. Switching plans takes effect immediately."
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

      {successMessage && (
        <div className="mb-6 rounded-2xl bg-emerald-50 px-4 py-3 text-sm font-medium text-emerald-700 ring-1 ring-emerald-200 dark:bg-emerald-950/30 dark:text-emerald-400 dark:ring-emerald-800">
          {successMessage}
        </div>
      )}

      {isLoading ? (
        <LoadingState title="Loading billing" rows={4} />
      ) : (
        <div className="space-y-6">
          {/* Current plan */}
          {summary && <CurrentPlanCard summary={summary} />}

          {/* Available plans */}
          {plans.length > 0 && (
            <div>
              <h2 className="mb-4 text-xl font-semibold tracking-tight text-foreground">
                Available plans
              </h2>
              <PlanComparison
                plans={plans}
                currentPlanName={summary?.subscription.plan_name}
                isChangingPlan={isChangingPlan}
                onChangePlan={(planName) => void changePlan(planName)}
              />
            </div>
          )}
        </div>
      )}
    </DashboardShell>
  );
}
