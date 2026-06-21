import type { Metadata } from "next";
import { BillingDashboard } from "../../../../components/billing/billing-dashboard";

type BillingPageProps = {
  params: Promise<{
    workspaceId: string;
  }>;
};

export const metadata: Metadata = {
  title: "Billing",
  description: "View and manage internal workspace billing plans.",
};

export default async function BillingPage({ params }: BillingPageProps) {
  const { workspaceId } = await params;

  return <BillingDashboard workspaceId={workspaceId} />;
}
