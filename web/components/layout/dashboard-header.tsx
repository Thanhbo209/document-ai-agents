type DashboardHeaderProps = {
  title: string;
  eyebrow?: string;
  description?: string;
  onOpenSidebar: () => void;
};

export function DashboardHeader({
  title,
  eyebrow,
  description,
  onOpenSidebar,
}: DashboardHeaderProps) {
  return (
    <header className="sticky top-0 z-30 border-b border-border/70 bg-background/86 backdrop-blur-xl">
      <div className="mx-auto flex max-w-7xl items-center justify-between gap-4 px-4 py-4 sm:px-6 lg:px-8">
        <div className="min-w-0">
          {eyebrow && (
            <p className="text-xs font-medium tracking-[0.18em] text-muted-foreground">
              {eyebrow}
            </p>
          )}
          <h1 className="mt-1 truncate text-xl font-semibold tracking-tight text-foreground">
            {title}
          </h1>
          {description && (
            <p className="mt-1 hidden max-w-2xl text-sm leading-6 text-muted-foreground md:block">
              {description}
            </p>
          )}
        </div>

        <button
          type="button"
          onClick={onOpenSidebar}
          className="inline-flex items-center rounded-xl border border-border bg-card px-3 py-2 text-sm font-medium text-card-foreground shadow-sm transition hover:-translate-y-0.5 hover:bg-accent active:translate-y-0 lg:hidden"
        >
          Menu
        </button>
      </div>
    </header>
  );
}
