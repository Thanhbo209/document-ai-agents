import { StatusBadge } from "../../ui/status-badge";

type OverviewHeroProps = {
  workspaceName: string;
  workspaceStatus: string;
  planName: string;
};

export function OverviewHero({
  workspaceName,
  workspaceStatus,
  planName,
}: OverviewHeroProps) {
  return (
    <div className="mb-8 flex flex-wrap items-end justify-between gap-4">
      <div>
        <p className="text-sm font-medium text-muted-foreground">Workspace</p>
        <h2 className="mt-1 text-3xl font-semibold tracking-tight text-balance text-foreground md:text-4xl">
          {workspaceName}
        </h2>
        <p className="mt-2 text-sm text-muted-foreground">
          Monitor health, usage, and activity at a glance.
        </p>
      </div>
      <div className="flex flex-wrap items-center gap-2">
        <StatusBadge status={workspaceStatus} />
        <span className="inline-flex items-center rounded-lg bg-primary/10 px-2.5 py-1 text-xs font-medium text-primary ring-1 ring-primary/20">
          {planName}
        </span>
      </div>
    </div>
  );
}
