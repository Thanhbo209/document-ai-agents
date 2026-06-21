import type { WorkspaceSettings } from "../../lib/workspace-settings-api";
import { formatDate, humanizeStatus, maskId } from "../../lib/format";
import { StatusBadge } from "../ui/status-badge";
import { SectionCard } from "../ui/section-card";

type WorkspaceOverviewCardProps = {
  settings: WorkspaceSettings;
};

export function WorkspaceOverviewCard({ settings }: WorkspaceOverviewCardProps) {
  return (
    <SectionCard>
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <p className="text-sm font-medium text-muted-foreground">Workspace</p>
          <h2 className="mt-1 text-3xl font-semibold tracking-tight text-card-foreground">
            {settings.name}
          </h2>
        </div>
        <StatusBadge status={settings.status} />
      </div>

      <dl className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <MetaItem
          label="Status"
          value={humanizeStatus(settings.status)}
        />
        {settings.plan && (
          <MetaItem
            label="Current plan"
            value={settings.plan.display_name}
          />
        )}
        {settings.deletion_requested_at && (
          <MetaItem
            label="Deletion requested"
            value={formatDate(settings.deletion_requested_at)}
          />
        )}
        {/* Show masked reference ID — not the raw UUID */}
        <div className="flex flex-col gap-0.5">
          <dt className="text-xs text-muted-foreground">Workspace reference</dt>
          <dd className="font-mono text-sm font-medium text-card-foreground">
            {maskId(settings.workspace_id)}
          </dd>
        </div>
      </dl>
    </SectionCard>
  );
}

function MetaItem({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex flex-col gap-0.5">
      <dt className="text-xs text-muted-foreground">{label}</dt>
      <dd className="text-sm font-medium text-card-foreground">{value}</dd>
    </div>
  );
}
