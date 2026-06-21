"use client";

import { useMemo, useState } from "react";
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
  const resolvedNavItems = useMemo(
    () =>
      navItems ??
      (workspaceId ? buildWorkspaceNavItems(workspaceId) : buildAdminNavItems()),
    [navItems, workspaceId],
  );

  return (
    <div className="min-h-dvh overflow-x-hidden bg-background text-foreground">
      <div className="pointer-events-none fixed inset-0 -z-10 bg-[radial-gradient(circle_at_top_left,color-mix(in_oklch,var(--chart-1)_20%,transparent),transparent_34rem),radial-gradient(circle_at_bottom_right,color-mix(in_oklch,var(--chart-5)_12%,transparent),transparent_28rem)]" />
      <div className="grid min-h-dvh lg:grid-cols-[18rem_1fr]">
        <div className="sticky top-0 hidden h-dvh border-r border-sidebar-border bg-sidebar lg:block">
          <DashboardSidebar
            navItems={resolvedNavItems}
            activeItem={activeItem}
            workspaceId={workspaceId}
            mode={mode}
          />
        </div>

        <div className="min-w-0">
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
      href: `/workspaces/${workspaceId}`,
      detail: "Health and activity",
    },
    {
      id: "documents",
      label: "Documents",
      href: `/workspaces/${workspaceId}#documents`,
      detail: "Upload and ingestion",
    },
    {
      id: "chat",
      label: "Chat",
      href: `/chat/${workspaceId}`,
      detail: "Grounded answers",
    },
    {
      id: "review",
      label: "Review",
      href: `/review/${workspaceId}`,
      detail: "Human decisions",
    },
    {
      id: "usage",
      label: "Usage",
      href: `/usage/${workspaceId}`,
      detail: "Quotas and limits",
    },
    {
      id: "billing",
      label: "Billing",
      href: `/billing/${workspaceId}`,
      detail: "Plans and policy",
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
      detail: "Tenant metadata",
      onClick: () => onSelect?.("workspaces"),
    },
    {
      id: "jobs",
      label: "Jobs",
      detail: "Ingestion status",
      onClick: () => onSelect?.("jobs"),
    },
    {
      id: "audit",
      label: "Audit events",
      detail: "Security trail",
      onClick: () => onSelect?.("audit"),
    },
  ];
}
