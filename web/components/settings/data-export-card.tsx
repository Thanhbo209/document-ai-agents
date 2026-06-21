import { Button } from "../ui/button";
import { SectionCard } from "../ui/section-card";

type DataExportCardProps = {
  isExporting: boolean;
  onExport: () => void;
};

export function DataExportCard({ isExporting, onExport }: DataExportCardProps) {
  return (
    <SectionCard>
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <p className="text-sm font-medium text-muted-foreground">
            Compliance and data controls
          </p>
          <h3 className="mt-1 text-2xl font-semibold tracking-tight text-card-foreground">
            Export workspace data
          </h3>
          <p className="mt-3 max-w-2xl text-sm leading-6 text-muted-foreground">
            Download a JSON file containing all workspace-owned records,
            including indexed document content, conversation messages, and
            audit-safe metadata. Internal system identifiers may be present in
            the export for data integrity purposes.
          </p>
        </div>
        <Button disabled={isExporting} onClick={onExport}>
          {isExporting ? "Preparing export\u2026" : "Download export"}
        </Button>
      </div>

      <ul className="mt-5 space-y-2">
        {[
          "Document titles, types, and indexing status",
          "Indexed chunks and content",
          "Conversation history",
          "Audit-safe metadata",
        ].map((item) => (
          <li key={item} className="flex items-center gap-2 text-sm text-muted-foreground">
            <svg
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
              className="h-4 w-4 shrink-0 text-emerald-500"
              aria-hidden="true"
            >
              <path d="m5 12 5 5L20 7" />
            </svg>
            {item}
          </li>
        ))}
      </ul>
    </SectionCard>
  );
}
