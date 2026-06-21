import type { Metadata } from "next";
import { WorkspaceSettingsDashboard } from "../../../../components/settings/workspace-settings-dashboard";

type SettingsPageProps = {
  params: Promise<{
    workspaceId: string;
  }>;
};

export const metadata: Metadata = {
  title: "Workspace Settings",
  description: "Manage workspace data export and lifecycle controls.",
};

export default async function SettingsPage({ params }: SettingsPageProps) {
  const { workspaceId } = await params;

  return <WorkspaceSettingsDashboard workspaceId={workspaceId} />;
}
