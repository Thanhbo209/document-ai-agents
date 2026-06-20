import type { Metadata } from "next";
import { WorkspaceUploadManager } from "../../../../components/workspaces/workspace-upload-manager";

type WorkspacePageProps = {
  params: Promise<{ workspaceId: string }>;
};

export const metadata: Metadata = {
  title: "Workspace",
  description: "Upload documents and monitor ingestion status.",
};

export default async function WorkspacePage({ params }: WorkspacePageProps) {
  const { workspaceId } = await params;

  return (
    <main className="min-h-screen bg-slate-50">
      <WorkspaceUploadManager workspaceId={workspaceId} />
    </main>
  );
}
