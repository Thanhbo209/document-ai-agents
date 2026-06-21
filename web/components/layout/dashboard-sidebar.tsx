import { DashboardNavItem, SidebarNavItem } from "./sidebar-nav-item";

type DashboardSidebarProps = {
  navItems: DashboardNavItem[];
  activeItem: string;
  workspaceId?: string;
  mode?: "workspace" | "admin";
  onNavigate?: () => void;
};

export function DashboardSidebar({
  navItems,
  activeItem,
  workspaceId,
  mode = "workspace",
  onNavigate,
}: DashboardSidebarProps) {
  return (
    <aside className="flex h-full flex-col bg-sidebar text-sidebar-foreground">
      <div className="px-4 py-5">
        <div className="flex items-center gap-3">
          <div className="grid h-10 w-10 place-items-center rounded-2xl bg-sidebar-primary text-sm font-semibold text-sidebar-primary-foreground shadow-sm">
            RP
          </div>
          <div>
            <p className="text-sm font-semibold">RAG Platform</p>
            <p className="text-xs text-sidebar-foreground/50">
              {mode === "admin" ? "Operations" : "Workspace"}
            </p>
          </div>
        </div>
      </div>

      <nav className="flex-1 space-y-1 px-3">
        {navItems.map((item) => (
          <SidebarNavItem
            key={item.id}
            item={item}
            isActive={activeItem === item.id}
            onNavigate={onNavigate}
          />
        ))}
      </nav>

      <div className="border-t border-sidebar-border p-4">
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
      </div>
    </aside>
  );
}
