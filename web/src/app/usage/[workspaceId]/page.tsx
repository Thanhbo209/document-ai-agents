import type { Metadata } from "next";
import { UsageDashboard } from "../../../../components/usage/usage-dashboard";

type UsagePageProps = {
  params: Promise<{
    workspaceId: string;
  }>;
};

export const metadata: Metadata = {
  title: "Usage",
  description: "View workspace usage, quotas, and cost controls.",
};

export default async function UsagePage({ params }: UsagePageProps) {
  const { workspaceId } = await params;

  return <UsageDashboard workspaceId={workspaceId} />;
}
