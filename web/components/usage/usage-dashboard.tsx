"use client";

import { useEffect, useState } from "react";
import { getWorkspaceUsage, UsageMetric, UsagePlan } from "../../lib/usage-api";
import { DashboardShell } from "../layout/dashboard-shell";
import { ErrorState } from "../ui/error-state";
import { LoadingState } from "../ui/loading-state";
import { PageHeader } from "../ui/page-header";
import { Button } from "../ui/button";
import { UsageHero } from "./usage-hero";
import { UsageProgressSection } from "./usage-progress-section";
import { UsagePlanCta } from "./usage-plan-cta";

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

  return (
    <DashboardShell
      activeItem="usage"
      title="Usage"
      description="Track quota pressure across storage, documents, queries, and token usage."
      workspaceId={workspaceId}
    >
      <PageHeader
        kicker="Usage"
        title="How much have you used?"
        description="All metrics reflect your current billing period. Limits come from your active plan."
        actions={
          <Button href={`/billing/${workspaceId}`} variant="secondary">
            Manage plan
          </Button>
        }
      />

      {errorMessage && (
        <div className="mb-6">
          <ErrorState message={errorMessage} />
        </div>
      )}

      {isLoading ? (
        <LoadingState title="Loading usage" rows={4} />
      ) : (
        <div className="space-y-6">
          {plan && (
            <UsageHero
              planDisplayName={plan.display_name}
              planStatus={plan.status}
            />
          )}

          <UsageProgressSection metrics={metrics} />

          {plan && (
            <UsagePlanCta
              planName={plan.display_name}
              billingHref={`/billing/${workspaceId}`}
            />
          )}
        </div>
      )}
    </DashboardShell>
  );
}
