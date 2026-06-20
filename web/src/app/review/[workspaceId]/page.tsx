import type { Metadata } from "next";
import { ReviewWorkflow } from "../../../../components/review/review-workflow";

type ReviewPageProps = {
  params: Promise<{
    workspaceId: string;
  }>;
};

export const metadata: Metadata = {
  title: "Review",
  description: "Review extracted values, generated reports, and agent actions.",
};

export default async function ReviewPage({ params }: ReviewPageProps) {
  const { workspaceId } = await params;

  return <ReviewWorkflow workspaceId={workspaceId} />;
}
