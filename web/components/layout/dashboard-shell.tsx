"use client";

import { useMemo, useState, useSyncExternalStore } from "react";
import {
  AuditIcon,
  BillingIcon,
  ChatIcon,
  DocumentsIcon,
  JobsIcon,
  OverviewIcon,
  ReviewIcon,
  SettingsIcon,
  UsageIcon,
  WorkspacesIcon,
} from "../icons/dashboard-icons";
import { DashboardHeader } from "./dashboard-header";
import { DashboardSidebar } from "./dashboard-sidebar";
import { MobileSidebar } from "./mobile-sidebar";
import { DashboardNavItem } from "./sidebar-nav-item";

type DashboardShellProps = {
  children: React.ReactNode;
  activeItem: string;
  title: string;
  description?: string;
  workspaceId?: string;
  mode?: "workspace" | "admin";
  navItems?: DashboardNavItem[];
};

const SIDEBAR_COLLAPSED_KEY = "rag-platform-sidebar-collapsed";
const SIDEBAR_COLLAPSED_EVENT = "rag-platform-sidebar-collapsed-change";

export function DashboardShell({
  children,
  activeItem,
  title,
  description,
  workspaceId,
  mode = "workspace",
  navItems,
}: DashboardShellProps) {
  const [isMobileOpen, setIsMobileOpen] = useState(false);
  const isSidebarCollapsed = useSyncExternalStore(
    subscribeToSidebarPreference,
    getSidebarCollapsedSnapshot,
    getServerSidebarCollapsedSnapshot,
  );

  const resolvedNavItems = useMemo(
    () =>
      navItems ??
      (workspaceId ? buildWorkspaceNavItems(workspaceId) : buildAdminNavItems()),
    [navItems, workspaceId],
  );

  function toggleSidebarCollapsed() {
    const nextValue = !getSidebarCollapsedSnapshot();
    window.localStorage.setItem(SIDEBAR_COLLAPSED_KEY, String(nextValue));
    window.dispatchEvent(new Event(SIDEBAR_COLLAPSED_EVENT));
  }

  return (
    <div className="min-h-dvh overflow-x-hidden bg-background text-foreground">
      <div className="pointer-events-none fixed inset-0 -z-10 bg-[radial-gradient(circle_at_top_left,color-mix(in_oklch,var(--chart-1)_20%,transparent),transparent_34rem),radial-gradient(circle_at_bottom_right,color-mix(in_oklch,var(--chart-5)_12%,transparent),transparent_28rem)]" />

      <div
        className={[
          "fixed left-0 top-0 z-40 hidden h-screen border-r border-sidebar-border bg-sidebar transition-[width] duration-300 lg:block",
          isSidebarCollapsed ? "w-20" : "w-72",
        ].join(" ")}
      >
        <DashboardSidebar
          navItems={resolvedNavItems}
          activeItem={activeItem}
          workspaceId={workspaceId}
          mode={mode}
          isCollapsed={isSidebarCollapsed}
          onToggleCollapsed={toggleSidebarCollapsed}
        />
      </div>

      <div
        className={[
          "min-w-0 transition-[padding] duration-300",
          isSidebarCollapsed ? "lg:pl-20" : "lg:pl-72",
        ].join(" ")}
      >
        <DashboardHeader
          title={title}
          eyebrow={mode === "admin" ? "Admin console" : "Workspace console"}
          description={description}
          onOpenSidebar={() => setIsMobileOpen(true)}
        />
        <main className="mx-auto w-full max-w-7xl px-4 py-6 sm:px-6 lg:px-8 lg:py-8">
          {children}
        </main>
      </div>

      <MobileSidebar
        isOpen={isMobileOpen}
        navItems={resolvedNavItems}
        activeItem={activeItem}
        workspaceId={workspaceId}
        mode={mode}
        onClose={() => setIsMobileOpen(false)}
      />
    </div>
  );
}

export function buildWorkspaceNavItems(workspaceId: string): DashboardNavItem[] {
  return [
    {
      id: "overview",
      label: "Overview",
      icon: OverviewIcon,
      href: `/workspaces/${workspaceId}`,
      detail: "Health and activity",
    },
    {
      id: "documents",
      label: "Documents",
      icon: DocumentsIcon,
      href: `/workspaces/${workspaceId}#documents`,
      detail: "Upload and ingestion",
    },
    {
      id: "chat",
      label: "Chat",
      icon: ChatIcon,
      href: `/chat/${workspaceId}`,
      detail: "Grounded answers",
    },
    {
      id: "review",
      label: "Review",
      icon: ReviewIcon,
      href: `/review/${workspaceId}`,
      detail: "Human decisions",
    },
    {
      id: "usage",
      label: "Usage",
      icon: UsageIcon,
      href: `/usage/${workspaceId}`,
      detail: "Quotas and limits",
    },
    {
      id: "billing",
      label: "Billing",
      icon: BillingIcon,
      href: `/billing/${workspaceId}`,
      detail: "Plans and policy",
    },
    {
      id: "settings",
      label: "Settings",
      icon: SettingsIcon,
      href: `/settings/${workspaceId}`,
      detail: "Data controls",
    },
  ];
}

export function buildAdminNavItems(
  onSelect?: (item: "workspaces" | "jobs" | "audit") => void,
): DashboardNavItem[] {
  return [
    {
      id: "workspaces",
      label: "Workspaces",
      icon: WorkspacesIcon,
      detail: "Tenant metadata",
      onClick: () => onSelect?.("workspaces"),
    },
    {
      id: "jobs",
      label: "Jobs",
      icon: JobsIcon,
      detail: "Ingestion status",
      onClick: () => onSelect?.("jobs"),
    },
    {
      id: "audit",
      label: "Audit events",
      icon: AuditIcon,
      detail: "Security trail",
      onClick: () => onSelect?.("audit"),
    },
  ];
}

function subscribeToSidebarPreference(callback: () => void) {
  window.addEventListener("storage", callback);
  window.addEventListener(SIDEBAR_COLLAPSED_EVENT, callback);

  return () => {
    window.removeEventListener("storage", callback);
    window.removeEventListener(SIDEBAR_COLLAPSED_EVENT, callback);
  };
}

function getSidebarCollapsedSnapshot(): boolean {
  return window.localStorage.getItem(SIDEBAR_COLLAPSED_KEY) === "true";
}

function getServerSidebarCollapsedSnapshot(): boolean {
  return false;
}
