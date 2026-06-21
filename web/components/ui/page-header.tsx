type PageHeaderProps = {
  title: string;
  description: string;
  kicker?: string;
  actions?: React.ReactNode;
  meta?: React.ReactNode;
};

export function PageHeader({
  title,
  description,
  kicker,
  actions,
  meta,
}: PageHeaderProps) {
  return (
    <section className="mb-8 grid gap-5 lg:grid-cols-[1fr_auto] lg:items-end">
      <div>
        {kicker && (
          <p className="text-sm font-medium text-muted-foreground">{kicker}</p>
        )}
        <h2 className="mt-2 max-w-3xl text-3xl font-semibold tracking-tight text-balance text-foreground md:text-4xl">
          {title}
        </h2>
        <p className="mt-3 max-w-2xl text-sm leading-6 text-pretty text-muted-foreground md:text-base">
          {description}
        </p>
        {meta && <div className="mt-4">{meta}</div>}
      </div>
      {actions && <div className="flex flex-wrap gap-2">{actions}</div>}
    </section>
  );
}
