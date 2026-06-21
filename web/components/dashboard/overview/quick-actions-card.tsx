import { SectionCard } from "../../ui/section-card";
import Link from "next/link";

type QuickActionsCardProps = {
  workspaceId: string;
};

type Action = {
  label: string;
  description: string;
  href: string;
  icon: React.ReactNode;
  variant: "primary" | "secondary";
};

export function QuickActionsCard({ workspaceId }: QuickActionsCardProps) {
  const actions: Action[] = [
    {
      label: "Upload document",
      description: "Add a new source file",
      href: `/documents/${workspaceId}`,
      icon: (
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" className="h-5 w-5" aria-hidden="true">
          <path d="M12 20V4" />
          <path d="M5 11l7-7 7 7" />
          <path d="M3 20h18" />
        </svg>
      ),
      variant: "primary",
    },
    {
      label: "Ask in chat",
      description: "Query your documents",
      href: `/chat/${workspaceId}`,
      icon: (
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" className="h-5 w-5" aria-hidden="true">
          <path d="M5 6.5A3.5 3.5 0 0 1 8.5 3h7A3.5 3.5 0 0 1 19 6.5v4A3.5 3.5 0 0 1 15.5 14H11l-4.5 4v-4.5A3.5 3.5 0 0 1 5 10.5v-4Z" />
        </svg>
      ),
      variant: "primary",
    },
    {
      label: "View documents",
      description: "Browse your library",
      href: `/documents/${workspaceId}`,
      icon: (
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" className="h-5 w-5" aria-hidden="true">
          <path d="M7 3.5h7l3 3V20a1 1 0 0 1-1 1H7a1 1 0 0 1-1-1V4.5a1 1 0 0 1 1-1Z" />
          <path d="M14 3.5V7h3" />
          <path d="M9 12h6" />
          <path d="M9 16h4" />
        </svg>
      ),
      variant: "secondary",
    },
    {
      label: "View usage",
      description: "Check quotas and limits",
      href: `/usage/${workspaceId}`,
      icon: (
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" className="h-5 w-5" aria-hidden="true">
          <path d="M4 19V5" />
          <path d="M4 19h16" />
          <path d="M8 16v-5" />
          <path d="M12 16V8" />
          <path d="M16 16v-3" />
        </svg>
      ),
      variant: "secondary",
    },
    {
      label: "Manage plan",
      description: "View billing and limits",
      href: `/billing/${workspaceId}`,
      icon: (
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" className="h-5 w-5" aria-hidden="true">
          <path d="M5 7.5A2.5 2.5 0 0 1 7.5 5h9A2.5 2.5 0 0 1 19 7.5v9A2.5 2.5 0 0 1 16.5 19h-9A2.5 2.5 0 0 1 5 16.5v-9Z" />
          <path d="M5 9h14" />
          <path d="M8.5 14h3" />
        </svg>
      ),
      variant: "secondary",
    },
    {
      label: "Settings",
      description: "Data controls and compliance",
      href: `/settings/${workspaceId}`,
      icon: (
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" className="h-5 w-5" aria-hidden="true">
          <path d="M12 8.5a3.5 3.5 0 1 0 0 7 3.5 3.5 0 0 0 0-7Z" />
          <path d="M19 12a7.6 7.6 0 0 0-.1-1.1l2-1.5-2-3.4-2.4 1a8 8 0 0 0-1.9-1.1L14.3 3h-4.6l-.3 2.9A8 8 0 0 0 7.5 7L5.1 6l-2 3.4 2 1.5A7.6 7.6 0 0 0 5 12c0 .4 0 .8.1 1.1l-2 1.5 2 3.4 2.4-1a8 8 0 0 0 1.9 1.1l.3 2.9h4.6l.3-2.9a8 8 0 0 0 1.9-1.1l2.4 1 2-3.4-2-1.5c.1-.3.1-.7.1-1.1Z" />
        </svg>
      ),
      variant: "secondary",
    },
  ];

  return (
    <SectionCard>
      <p className="text-sm font-medium text-muted-foreground">Jump to</p>
      <h3 className="mt-1 text-xl font-semibold tracking-tight text-card-foreground">
        Quick actions
      </h3>

      <div className="mt-5 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {actions.map((action) => (
          <Link
            key={action.href + action.label}
            href={action.href}
            className={[
              "group flex items-center gap-3 rounded-2xl border p-4 text-left transition duration-200",
              "hover:-translate-y-0.5 hover:shadow-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
              action.variant === "primary"
                ? "border-primary/20 bg-primary/6 text-primary hover:bg-primary/10"
                : "border-border bg-background text-card-foreground hover:bg-accent",
            ].join(" ")}
          >
            <span
              className={[
                "flex h-9 w-9 shrink-0 items-center justify-center rounded-xl transition",
                action.variant === "primary"
                  ? "bg-primary/12 text-primary"
                  : "bg-muted text-muted-foreground group-hover:text-accent-foreground",
              ].join(" ")}
            >
              {action.icon}
            </span>
            <span className="min-w-0">
              <span className="block text-sm font-semibold">{action.label}</span>
              <span className="block text-xs text-muted-foreground">
                {action.description}
              </span>
            </span>
          </Link>
        ))}
      </div>
    </SectionCard>
  );
}
