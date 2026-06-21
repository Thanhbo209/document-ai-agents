"use client";

import { MoonIcon, SunIcon } from "../icons/dashboard-icons";
import { useTheme } from "./theme-provider";

type ThemeToggleProps = {
  showLabel?: boolean;
};

export function ThemeToggle({ showLabel = true }: ThemeToggleProps) {
  const { theme, toggleTheme } = useTheme();
  const isDark = theme === "dark";
  const label = isDark ? "Switch to light mode" : "Switch to dark mode";
  const Icon = isDark ? SunIcon : MoonIcon;

  return (
    <button
      type="button"
      aria-label={label}
      title={label}
      onClick={toggleTheme}
      className={[
        "inline-flex w-full items-center gap-3 rounded-xl border border-sidebar-border bg-sidebar-accent px-3 py-2.5 text-sm font-medium text-sidebar-accent-foreground transition duration-200",
        "hover:-translate-y-0.5 hover:bg-sidebar-accent/80 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sidebar-ring active:translate-y-0",
        showLabel ? "justify-start" : "justify-center px-2.5",
      ].join(" ")}
    >
      <Icon className="h-4 w-4 shrink-0" />
      {showLabel && <span>{isDark ? "Light mode" : "Dark mode"}</span>}
    </button>
  );
}
