import Link from "next/link";

export type DashboardNavItem = {
  id: string;
  label: string;
  href?: string;
  detail?: string;
  onClick?: () => void;
};

type SidebarNavItemProps = {
  item: DashboardNavItem;
  isActive: boolean;
  onNavigate?: () => void;
};

export function SidebarNavItem({
  item,
  isActive,
  onNavigate,
}: SidebarNavItemProps) {
  const className = [
    "group flex w-full items-center justify-between rounded-xl px-3 py-2.5 text-left text-sm transition duration-200",
    "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
    isActive
      ? "bg-sidebar-primary text-sidebar-primary-foreground shadow-sm"
      : "text-sidebar-foreground/72 hover:bg-sidebar-accent hover:text-sidebar-accent-foreground",
  ].join(" ");

  const content = (
    <>
      <span>
        <span className="block font-medium">{item.label}</span>
        {item.detail && (
          <span
            className={[
              "mt-0.5 block text-[11px]",
              isActive
                ? "text-sidebar-primary-foreground/70"
                : "text-sidebar-foreground/42",
            ].join(" ")}
          >
            {item.detail}
          </span>
        )}
      </span>
      <span
        className={[
          "h-1.5 w-1.5 rounded-full transition",
          isActive ? "bg-sidebar-primary-foreground" : "bg-transparent",
        ].join(" ")}
      />
    </>
  );

  if (item.href) {
    return (
      <Link href={item.href} className={className} onClick={onNavigate}>
        {content}
      </Link>
    );
  }

  return (
    <button
      type="button"
      className={className}
      onClick={() => {
        item.onClick?.();
        onNavigate?.();
      }}
    >
      {content}
    </button>
  );
}
