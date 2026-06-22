"use client";

import { FileCardIcon } from "../documents/document-file-icon";

export type ImportSourceOption = {
  id: string;
  label: string;
  description: string;
  iconType: string;
  detail: string;
};

type ImportSourceSelectorProps = {
  options: ImportSourceOption[];
  selectedId: string;
  disabled?: boolean;
  onSelect: (id: string) => void;
};

export function ImportSourceSelector({
  options,
  selectedId,
  disabled = false,
  onSelect,
}: ImportSourceSelectorProps) {
  return (
    <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
      {options.map((option) => {
        const isSelected = option.id === selectedId;

        return (
          <button
            key={option.id}
            type="button"
            disabled={disabled}
            onClick={() => onSelect(option.id)}
            className={[
              "group flex min-h-32 flex-col rounded-2xl border p-4 text-left transition duration-200",
              "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:pointer-events-none disabled:opacity-60",
              isSelected
                ? "border-primary/50 bg-primary/10 shadow-sm"
                : "border-border bg-background/70 hover:-translate-y-0.5 hover:bg-accent",
            ].join(" ")}
            aria-pressed={isSelected}
          >
            <FileCardIcon
              sourceType={option.iconType}
              size={38}
              className="mb-3"
            />
            <span className="text-sm font-semibold text-card-foreground">
              {option.label}
            </span>
            <span className="mt-1 text-xs leading-5 text-muted-foreground">
              {option.description}
            </span>
            <span className="mt-auto pt-3 text-[11px] font-medium uppercase tracking-[0.16em] text-muted-foreground">
              {option.detail}
            </span>
          </button>
        );
      })}
    </div>
  );
}
