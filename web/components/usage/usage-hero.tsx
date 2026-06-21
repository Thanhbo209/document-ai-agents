import { StatusBadge } from "../ui/status-badge";
import { SectionCard } from "../ui/section-card";

type UsageHeroProps = {
  planDisplayName: string;
  planStatus: string;
};

export function UsageHero({ planDisplayName, planStatus }: UsageHeroProps) {
  return (
    <SectionCard>
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="text-sm font-medium text-muted-foreground">
            Active plan
          </p>
          <h2 className="mt-2 text-4xl font-semibold tracking-tight text-card-foreground">
            {planDisplayName}
          </h2>
          <p className="mt-2 max-w-xl text-sm leading-6 text-muted-foreground">
            Monitor how much of your plan quota you have used. Metrics update
            after each upload, query, or indexing job.
          </p>
        </div>
        <StatusBadge status={planStatus} />
      </div>
    </SectionCard>
  );
}
