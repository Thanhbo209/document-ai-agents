"use client";

import { DashboardSidebar } from "./dashboard-sidebar";
import { DashboardNavItem } from "./sidebar-nav-item";

type MobileSidebarProps = {
  isOpen: boolean;
  navItems: DashboardNavItem[];
  activeItem: string;
  workspaceId?: string;
  mode?: "workspace" | "admin";
  onClose: () => void;
};

export function MobileSidebar({
  isOpen,
  navItems,
  activeItem,
  workspaceId,
  mode,
  onClose,
}: MobileSidebarProps) {
  if (!isOpen) {
    return null;
  }

  return (
    <div className="fixed inset-0 z-50 lg:hidden">
      <button
        type="button"
        aria-label="Close navigation"
        className="absolute inset-0 bg-foreground/30 backdrop-blur-sm"
        onClick={onClose}
      />
      <div className="relative h-full w-80 max-w-[86vw] border-r border-sidebar-border shadow-2xl">
        <DashboardSidebar
          navItems={navItems}
          activeItem={activeItem}
          workspaceId={workspaceId}
          mode={mode}
          showCollapseToggle={false}
          onNavigate={onClose}
        />
      </div>
    </div>
  );
}
