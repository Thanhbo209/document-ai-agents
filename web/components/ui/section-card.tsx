type SectionCardProps = {
  children: React.ReactNode;
  className?: string;
  /** If true, removes default padding so children control their own layout */
  noPadding?: boolean;
};

/**
 * Consistent card container used across all dashboard pages.
 * Provides rounded corners, soft border, subtle shadow, and dark/light support.
 */
export function SectionCard({
  children,
  className = "",
  noPadding = false,
}: SectionCardProps) {
  return (
    <section
      className={[
        "rounded-3xl bg-card shadow-sm ring-1 ring-border/70",
        noPadding ? "" : "p-6",
        className,
      ]
        .filter(Boolean)
        .join(" ")}
    >
      {children}
    </section>
  );
}
