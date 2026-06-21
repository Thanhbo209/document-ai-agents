import { WorkspaceDocument } from "../../lib/upload-api";
import { StatCard } from "../ui/stat-card";

type JobProgressCardsProps = {
  documents: WorkspaceDocument[];
};

export function JobProgressCards({ documents }: JobProgressCardsProps) {
  const total = documents.length;
  const indexed = documents.filter(
    (document) => document.status === "indexed",
  ).length;
  const processing = documents.filter(
    (document) => document.status === "processing",
  ).length;
  const failed = documents.filter(
    (document) => document.status === "failed",
  ).length;

  const cards = [
    {
      label: "Total documents",
      value: total,
    },
    {
      label: "Indexed",
      value: indexed,
    },
    {
      label: "Processing",
      value: processing,
    },
    {
      label: "Failed",
      value: failed,
    },
  ];

  return (
    <section className="grid grid-flow-dense gap-4 sm:grid-cols-2 xl:grid-cols-4">
      <StatCard
        label="Total documents"
        value={cards[0].value}
        detail="Files registered in this workspace"
      />
      <StatCard
        label="Indexed"
        value={cards[1].value}
        detail="Ready for grounded chat"
        tone="good"
      />
      <StatCard
        label="Processing"
        value={cards[2].value}
        detail="Currently moving through ingestion"
        tone="warning"
      />
      <StatCard
        label="Failed"
        value={cards[3].value}
        detail="Needs operator attention"
        tone={failed > 0 ? "danger" : "neutral"}
      />
    </section>
  );
}
