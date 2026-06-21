import { Button } from "../ui/button";
import { SectionCard } from "../ui/section-card";

type UsagePlanCtaProps = {
  planName: string;
  billingHref: string;
};

export function UsagePlanCta({ planName, billingHref }: UsagePlanCtaProps) {
  const isFree =
    planName.toLowerCase() === "free" ||
    planName.toLowerCase().includes("free");

  if (!isFree) {
    return (
      <SectionCard>
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <p className="text-sm font-medium text-muted-foreground">
              {planName} plan
            </p>
            <p className="mt-1 text-base font-semibold text-card-foreground">
              Your workspace has expanded limits.
            </p>
            <p className="mt-1 text-sm text-muted-foreground">
              Review your plan details and current limits on the billing page.
            </p>
          </div>
          <Button href={billingHref} variant="secondary">
            Manage plan
          </Button>
        </div>
      </SectionCard>
    );
  }

  return (
    <SectionCard className="ring-primary/20">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <p className="text-sm font-medium text-primary">Free plan</p>
          <p className="mt-1 text-base font-semibold text-card-foreground">
            Need more capacity?
          </p>
          <p className="mt-1 text-sm text-muted-foreground">
            The free plan has lower limits on storage, queries, and tokens.
            Upgrade to unlock higher quotas.
          </p>
        </div>
        <Button href={billingHref}>View plans</Button>
      </div>
    </SectionCard>
  );
}
