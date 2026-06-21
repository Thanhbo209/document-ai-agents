import Link from "next/link";
import type { DashboardIcon } from "../icons/dashboard-icons";

export type DashboardNavItem = {
  id: string;
  label: string;
  icon: DashboardIcon;
  href?: string;
  detail?: string;
  onClick?: () => void;
};

type SidebarNavItemProps = {
  item: DashboardNavItem;
  isActive: boolean;
  isCollapsed?: boolean;
  onNavigate?: () => void;
};

export function SidebarNavItem({
  item,
  isActive,
  isCollapsed = false,
  onNavigate,
}: SidebarNavItemProps) {
  const Icon = item.icon;
  const className = [
    "group flex w-full items-center rounded-xl text-left text-sm transition duration-200",
    "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
    isCollapsed ? "justify-center px-2.5 py-3" : "justify-between px-3 py-2.5",
    isActive
      ? "bg-primary text-primary-foreground shadow-sm"
      : "text-foreground/72 hover:bg-sidebar-accent hover:text-sidebar-accent-foreground",
  ].join(" ");

  const content = (
    <>
      <span className="flex min-w-0 items-center gap-3">
        <Icon className="h-5 w-5 shrink-0" />
        <span className={isCollapsed ? "sr-only" : "min-w-0"}>
          <span className="block truncate font-medium">{item.label}</span>
          {item.detail && (
            <span
              className={[
                "mt-0.5 block truncate text-[11px]",
                isActive ? "text-primary-foreground/70" : "text-foreground/42",
              ].join(" ")}
            >
              {item.detail}
            </span>
          )}
        </span>
      </span>

      {!isCollapsed && (
        <span
          className={[
            "h-1.5 w-1.5 rounded-full transition",
            isActive ? "bg-primary-foreground" : "bg-transparent",
          ].join(" ")}
        />
      )}

      {isCollapsed && isActive && (
        <span className="absolute right-1 h-5 w-1 rounded-full bg-primary-foreground" />
      )}
    </>
  );

  const sharedProps = {
    title: isCollapsed ? item.label : undefined,
    "aria-current": isActive ? ("page" as const) : undefined,
  };

  if (item.href) {
    return (
      <Link
        href={item.href}
        className={`relative ${className}`}
        onClick={() => {
          item.onClick?.();
          onNavigate?.();
        }}
        {...sharedProps}
      >
        {content}
      </Link>
    );
  }

  return (
    <button
      type="button"
      className={`relative ${className}`}
      onClick={() => {
        item.onClick?.();
        onNavigate?.();
      }}
      {...sharedProps}
    >
      {content}
    </button>
  );
}
