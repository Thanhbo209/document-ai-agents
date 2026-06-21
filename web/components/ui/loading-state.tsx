type LoadingStateProps = {
  title?: string;
  rows?: number;
};

export function LoadingState({
  title = "Loading",
  rows = 4,
}: LoadingStateProps) {
  return (
    <div className="rounded-3xl bg-card p-6 shadow-sm ring-1 ring-border/70">
      <p className="text-sm font-medium text-muted-foreground">{title}</p>
      <div className="mt-5 space-y-3">
        {Array.from({ length: rows }).map((_, index) => (
          <div
            key={index}
            className="h-12 animate-pulse rounded-2xl bg-muted"
            style={{ opacity: 1 - index * 0.1 }}
          />
        ))}
      </div>
    </div>
  );
}
