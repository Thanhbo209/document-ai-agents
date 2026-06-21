type EmptyStateProps = {
  title: string;
  description: string;
  action?: React.ReactNode;
  icon?: React.ReactNode;
};

export function EmptyState({ title, description, action, icon }: EmptyStateProps) {
  return (
    <div className="rounded-3xl border border-dashed border-border bg-card/72 p-10 text-center shadow-sm">
      <div className="mx-auto mb-5 flex h-14 w-14 items-center justify-center rounded-2xl bg-muted text-muted-foreground">
        {icon ?? (
          <svg
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.6"
            strokeLinecap="round"
            strokeLinejoin="round"
            className="h-7 w-7"
            aria-hidden="true"
          >
            <path d="M9 13h6m-3-3v6m-7 4h14a2 2 0 0 0 2-2V7l-5-5H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2Z" />
          </svg>
        )}
      </div>
      <h3 className="text-lg font-semibold text-card-foreground">{title}</h3>
      <p className="mx-auto mt-2 max-w-md text-sm leading-6 text-muted-foreground">
        {description}
      </p>
      {action && <div className="mt-6 flex justify-center">{action}</div>}
    </div>
  );
}
