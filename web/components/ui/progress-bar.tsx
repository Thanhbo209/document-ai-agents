import type { UsageTone } from "../../lib/format";

type ProgressBarProps = {
  value: number;
  max: number;
  tone?: UsageTone;
  showLabel?: boolean;
  label?: string;
  className?: string;
};

const toneTrack: Record<UsageTone, string> = {
  healthy: "bg-emerald-500",
  warning: "bg-amber-500",
  danger: "bg-orange-500",
  exceeded: "bg-destructive",
};

const toneText: Record<UsageTone, string> = {
  healthy: "text-emerald-600",
  warning: "text-amber-600",
  danger: "text-orange-600",
  exceeded: "text-destructive",
};

export function ProgressBar({
  value,
  max,
  tone = "healthy",
  showLabel = false,
  label,
  className = "",
}: ProgressBarProps) {
  const pct = max > 0 ? Math.min(100, Math.round((value / max) * 100)) : 0;

  return (
    <div className={className}>
      {(showLabel || label) && (
        <div className="mb-1.5 flex items-center justify-between gap-2">
          {label && (
            <span className="text-xs font-medium text-muted-foreground">
              {label}
            </span>
          )}
          {showLabel && (
            <span className={`text-xs font-semibold tabular-nums ${toneText[tone]}`}>
              {pct}%
            </span>
          )}
        </div>
      )}
      <div className="h-2 w-full overflow-hidden rounded-full bg-muted">
        <div
          className={`h-full rounded-full transition-all duration-700 ${toneTrack[tone]}`}
          style={{ width: `${pct}%` }}
          role="progressbar"
          aria-valuenow={value}
          aria-valuemin={0}
          aria-valuemax={max}
        />
      </div>
    </div>
  );
}
