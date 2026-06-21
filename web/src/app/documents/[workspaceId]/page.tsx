import type { Metadata } from "next";
import { DocumentsManager } from "../../../../components/documents/documents-manager";

type DocumentsPageProps = {
  params: Promise<{ workspaceId: string }>;
};

export const metadata: Metadata = {
  title: "Documents",
  description: "Browse, search, and manage all indexed documents in your workspace.",
};

export default async function DocumentsPage({ params }: DocumentsPageProps) {
  const { workspaceId } = await params;

  return <DocumentsManager workspaceId={workspaceId} />;
}
