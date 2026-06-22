"use client";

import { Button } from "../ui/button";

type UrlImportFormProps = {
  label: string;
  title: string;
  description: string;
  placeholder: string;
  value: string;
  isBusy?: boolean;
  submitLabel: string;
  helperText?: string;
  onChange: (value: string) => void;
  onSubmit: () => void;
};

export function UrlImportForm({
  label,
  title,
  description,
  placeholder,
  value,
  isBusy = false,
  submitLabel,
  helperText,
  onChange,
  onSubmit,
}: UrlImportFormProps) {
  return (
    <form
      className="rounded-2xl border border-border bg-background/70 p-5"
      onSubmit={(event) => {
        event.preventDefault();
        onSubmit();
      }}
    >
      <div>
        <p className="text-sm font-semibold text-card-foreground">{title}</p>
        <p className="mt-1 text-sm leading-6 text-muted-foreground">
          {description}
        </p>
      </div>

      <label
        htmlFor="source-url"
        className="mt-5 block text-sm font-medium text-card-foreground"
      >
        {label}
      </label>
      <div className="mt-2 flex flex-col gap-3 sm:flex-row">
        <input
          id="source-url"
          type="url"
          value={value}
          onChange={(event) => onChange(event.target.value)}
          placeholder={placeholder}
          disabled={isBusy}
          className="min-w-0 flex-1 rounded-xl border border-input bg-card px-4 py-3 text-sm outline-none transition focus:ring-2 focus:ring-ring disabled:opacity-60"
        />
        <Button type="submit" disabled={isBusy || !value.trim()}>
          {isBusy ? "Importing..." : submitLabel}
        </Button>
      </div>

      {helperText && (
        <p className="mt-3 text-xs leading-5 text-muted-foreground">
          {helperText}
        </p>
      )}
    </form>
  );
}
