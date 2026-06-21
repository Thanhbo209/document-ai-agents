import Link from "next/link";

type ButtonVariant = "primary" | "secondary" | "danger" | "quiet";

type ButtonProps = {
  children: React.ReactNode;
  variant?: ButtonVariant;
  className?: string;
  disabled?: boolean;
  type?: "button" | "submit";
  href?: string;
  onClick?: () => void;
};

export function Button({
  children,
  variant = "primary",
  className = "",
  disabled = false,
  type = "button",
  href,
  onClick,
}: ButtonProps) {
  const classes = [
    "inline-flex items-center justify-center rounded-xl px-4 py-2.5 text-sm font-medium transition duration-200",
    "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:pointer-events-none disabled:opacity-50",
    "hover:-translate-y-0.5 active:translate-y-0",
    variantClasses[variant],
    className,
  ].join(" ");

  if (href) {
    return (
      <Link href={href} className={classes}>
        {children}
      </Link>
    );
  }

  return (
    <button
      type={type}
      disabled={disabled}
      onClick={onClick}
      className={classes}
    >
      {children}
    </button>
  );
}

const variantClasses: Record<ButtonVariant, string> = {
  primary: "bg-primary text-primary-foreground shadow-sm hover:bg-primary/88",
  secondary:
    "border border-border bg-card text-card-foreground shadow-sm hover:bg-accent",
  danger:
    "bg-destructive text-destructive-foreground shadow-sm hover:bg-destructive/88",
  quiet: "text-muted-foreground hover:bg-accent hover:text-accent-foreground",
};
