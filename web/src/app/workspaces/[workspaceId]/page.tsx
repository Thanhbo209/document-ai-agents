import type { Metadata } from "next";
import { WorkspaceUploadManager } from "../../../../components/workspaces/workspace-upload-manager";

type WorkspacePageProps = {
  params: Promise<{ workspaceId: string }>;
};

export const metadata: Metadata = {
  title: "Overview",
  description: "Workspace health, usage, and activity at a glance.",
};

export default async function WorkspacePage({ params }: WorkspacePageProps) {
  const { workspaceId } = await params;

  return <WorkspaceUploadManager workspaceId={workspaceId} />;
}
