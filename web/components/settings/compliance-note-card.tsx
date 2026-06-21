import { SectionCard } from "../ui/section-card";

export function ComplianceNoteCard() {
  return (
    <SectionCard>
      <div className="flex items-start gap-3">
        <svg
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.8"
          strokeLinecap="round"
          strokeLinejoin="round"
          className="mt-0.5 h-5 w-5 shrink-0 text-muted-foreground"
          aria-hidden="true"
        >
          <path d="M12 3 5 6v5c0 4.5 2.8 7.5 7 10 4.2-2.5 7-5.5 7-10V6l-7-3Z" />
          <path d="m9 12 2 2 4-4" />
        </svg>
        <div>
          <p className="text-sm font-semibold text-card-foreground">
            Audit logging is active
          </p>
          <p className="mt-1.5 max-w-2xl text-sm leading-6 text-muted-foreground">
            All significant workspace actions — including uploads, exports,
            plan changes, and deletion requests — are recorded in a secure
            audit trail. These logs are available to platform administrators
            for compliance and security review.
          </p>
        </div>
      </div>
    </SectionCard>
  );
}
