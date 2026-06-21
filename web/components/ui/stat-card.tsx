type StatCardProps = {
  label: string;
  value: string | number;
  detail?: string;
  tone?: "neutral" | "good" | "warning" | "danger";
  icon?: React.ReactNode;
};

export function StatCard({
  label,
  value,
  detail,
  tone = "neutral",
  icon,
}: StatCardProps) {
  return (
    <article className="group rounded-3xl bg-card p-5 shadow-sm ring-1 ring-border/70 transition duration-200 hover:-translate-y-1 hover:shadow-md">
      <div className="flex items-start justify-between gap-4">
        <p className="text-sm font-medium text-muted-foreground">{label}</p>
        <div className="flex shrink-0 items-center gap-2">
          {icon && (
            <span className="flex h-8 w-8 items-center justify-center rounded-xl bg-muted text-muted-foreground">
              {icon}
            </span>
          )}
          <span className={`h-2.5 w-2.5 rounded-full ${toneClasses[tone]}`} />
        </div>
      </div>
      <p className="mt-4 font-mono text-3xl font-semibold tracking-tight tabular-nums text-card-foreground">
        {value}
      </p>
      {detail && (
        <p className="mt-2 text-sm leading-5 text-muted-foreground">{detail}</p>
      )}
    </article>
  );
}

const toneClasses = {
  neutral: "bg-muted-foreground/35",
  good: "bg-emerald-500",
  warning: "bg-amber-500",
  danger: "bg-destructive",
};
