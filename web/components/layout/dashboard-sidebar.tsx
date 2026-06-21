import { DashboardNavItem, SidebarNavItem } from "./sidebar-nav-item";
import { ChevronIcon } from "../icons/dashboard-icons";
import { ThemeToggle } from "../theme/theme-toggle";

type DashboardSidebarProps = {
  navItems: DashboardNavItem[];
  activeItem: string;
  workspaceId?: string;
  mode?: "workspace" | "admin";
  isCollapsed?: boolean;
  showCollapseToggle?: boolean;
  onToggleCollapsed?: () => void;
  onNavigate?: () => void;
};

export function DashboardSidebar({
  navItems,
  activeItem,
  workspaceId,
  mode = "workspace",
  isCollapsed = false,
  showCollapseToggle = true,
  onToggleCollapsed,
  onNavigate,
}: DashboardSidebarProps) {
  return (
    <aside className="flex h-full min-h-0 flex-col bg-sidebar text-sidebar-foreground">
      <div
        className={[
          "flex items-center px-4 py-5",
          isCollapsed ? "justify-center" : "justify-between",
        ].join(" ")}
      >
        <div
          className={[
            "flex min-w-0 items-center gap-3",
            isCollapsed ? "justify-center" : "",
          ].join(" ")}
        >
          {!isCollapsed && (
            <div className="min-w-0">
              <p className="text-sm font-semibold">RAG Platform</p>
              <p className="text-xs text-sidebar-foreground/50">
                {mode === "admin" ? "Operations" : "Workspace"}
              </p>
            </div>
          )}
        </div>

        {showCollapseToggle && (
          <button
            type="button"
            aria-label={isCollapsed ? "Expand sidebar" : "Collapse sidebar"}
            title={isCollapsed ? "Expand sidebar" : "Collapse sidebar"}
            onClick={onToggleCollapsed}
            className="hidden h-9 w-9 shrink-0 items-center justify-center rounded-xl border border-sidebar-border bg-sidebar-accent text-sidebar-accent-foreground transition duration-200 hover:-translate-y-0.5 hover:bg-sidebar-accent/80 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sidebar-ring active:translate-y-0 lg:inline-flex"
          >
            <ChevronIcon
              className={[
                "h-4 w-4 transition-transform duration-300",
                isCollapsed ? "rotate-180" : "",
              ].join(" ")}
            />
          </button>
        )}
      </div>

      <nav
        className={[
          "flex-1 space-y-1 overflow-y-auto px-3 pb-3",
          isCollapsed ? "px-2" : "",
        ].join(" ")}
      >
        {navItems.map((item) => (
          <SidebarNavItem
            key={item.id}
            item={item}
            isActive={activeItem === item.id}
            isCollapsed={isCollapsed}
            onNavigate={onNavigate}
          />
        ))}
      </nav>

      <div
        className={[
          "space-y-3 border-t border-sidebar-border p-4",
          isCollapsed ? "px-2" : "",
        ].join(" ")}
      >
        <ThemeToggle showLabel={!isCollapsed} />

        {!isCollapsed && (
          <div className="rounded-2xl bg-sidebar-accent px-3 py-3">
            <p className="text-xs font-medium text-sidebar-accent-foreground">
              {mode === "admin" ? "Privacy boundary" : "Active workspace"}
            </p>
            <p className="mt-1 break-all font-mono text-[11px] text-sidebar-foreground/55">
              {mode === "admin"
                ? "Metadata only. No private document text."
                : (workspaceId ?? "No workspace")}
            </p>
          </div>
        )}
      </div>
    </aside>
  );
}
