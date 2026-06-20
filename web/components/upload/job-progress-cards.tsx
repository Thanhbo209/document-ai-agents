import { WorkspaceDocument } from "../../lib/api";

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
    <section className="grid gap-4 md:grid-cols-4">
      {cards.map((card) => (
        <div
          key={card.label}
          className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm"
        >
          <p className="text-sm text-slate-500">{card.label}</p>
          <p className="mt-2 text-3xl font-bold text-slate-900">{card.value}</p>
        </div>
      ))}
    </section>
  );
}
