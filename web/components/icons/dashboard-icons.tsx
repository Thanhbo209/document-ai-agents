import type { SVGProps } from "react";

export type DashboardIcon = (props: SVGProps<SVGSVGElement>) => React.ReactNode;

type IconProps = SVGProps<SVGSVGElement>;

function IconShell({ children, ...props }: IconProps) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      {...props}
    >
      {children}
    </svg>
  );
}

export function OverviewIcon(props: IconProps) {
  return (
    <IconShell {...props}>
      <path d="M4 11.5 12 4l8 7.5" />
      <path d="M6.5 10.5V20h11v-9.5" />
      <path d="M10 20v-5h4v5" />
    </IconShell>
  );
}

export function DocumentsIcon(props: IconProps) {
  return (
    <IconShell {...props}>
      <path d="M7 3.5h7l3 3V20a1 1 0 0 1-1 1H7a1 1 0 0 1-1-1V4.5a1 1 0 0 1 1-1Z" />
      <path d="M14 3.5V7h3" />
      <path d="M9 12h6" />
      <path d="M9 16h4" />
    </IconShell>
  );
}

export function ChatIcon(props: IconProps) {
  return (
    <IconShell {...props}>
      <path d="M5 6.5A3.5 3.5 0 0 1 8.5 3h7A3.5 3.5 0 0 1 19 6.5v4A3.5 3.5 0 0 1 15.5 14H11l-4.5 4v-4.5A3.5 3.5 0 0 1 5 10.5v-4Z" />
      <path d="M9 7.5h6" />
      <path d="M9 10.5h4" />
    </IconShell>
  );
}

export function ReviewIcon(props: IconProps) {
  return (
    <IconShell {...props}>
      <path d="M7 4h10a1 1 0 0 1 1 1v14l-3-2-3 2-3-2-3 2V5a1 1 0 0 1 1-1Z" />
      <path d="m9 11 2 2 4-5" />
    </IconShell>
  );
}

export function UsageIcon(props: IconProps) {
  return (
    <IconShell {...props}>
      <path d="M4 19V5" />
      <path d="M4 19h16" />
      <path d="M8 16v-5" />
      <path d="M12 16V8" />
      <path d="M16 16v-3" />
    </IconShell>
  );
}

export function BillingIcon(props: IconProps) {
  return (
    <IconShell {...props}>
      <path d="M5 7.5A2.5 2.5 0 0 1 7.5 5h9A2.5 2.5 0 0 1 19 7.5v9A2.5 2.5 0 0 1 16.5 19h-9A2.5 2.5 0 0 1 5 16.5v-9Z" />
      <path d="M5 9h14" />
      <path d="M8.5 14h3" />
    </IconShell>
  );
}

export function WorkspacesIcon(props: IconProps) {
  return (
    <IconShell {...props}>
      <path d="M4 7a2 2 0 0 1 2-2h5v6H4V7Z" />
      <path d="M13 5h5a2 2 0 0 1 2 2v3h-7V5Z" />
      <path d="M4 13h7v6H6a2 2 0 0 1-2-2v-4Z" />
      <path d="M13 13h7v4a2 2 0 0 1-2 2h-5v-6Z" />
    </IconShell>
  );
}

export function JobsIcon(props: IconProps) {
  return (
    <IconShell {...props}>
      <path d="M7 7h10" />
      <path d="M7 12h10" />
      <path d="M7 17h6" />
      <path d="M4 7h.01" />
      <path d="M4 12h.01" />
      <path d="M4 17h.01" />
    </IconShell>
  );
}

export function AuditIcon(props: IconProps) {
  return (
    <IconShell {...props}>
      <path d="M12 3 5 6v5c0 4.5 2.8 7.5 7 10 4.2-2.5 7-5.5 7-10V6l-7-3Z" />
      <path d="M9 12h6" />
      <path d="M12 9v6" />
    </IconShell>
  );
}

export function SettingsIcon(props: IconProps) {
  return (
    <IconShell {...props}>
      <path d="M12 8.5a3.5 3.5 0 1 0 0 7 3.5 3.5 0 0 0 0-7Z" />
      <path d="M19 12a7.6 7.6 0 0 0-.1-1.1l2-1.5-2-3.4-2.4 1a8 8 0 0 0-1.9-1.1L14.3 3h-4.6l-.3 2.9A8 8 0 0 0 7.5 7L5.1 6l-2 3.4 2 1.5A7.6 7.6 0 0 0 5 12c0 .4 0 .8.1 1.1l-2 1.5 2 3.4 2.4-1a8 8 0 0 0 1.9 1.1l.3 2.9h4.6l.3-2.9a8 8 0 0 0 1.9-1.1l2.4 1 2-3.4-2-1.5c.1-.3.1-.7.1-1.1Z" />
    </IconShell>
  );
}

export function MenuIcon(props: IconProps) {
  return (
    <IconShell {...props}>
      <path d="M4 7h16" />
      <path d="M4 12h16" />
      <path d="M4 17h16" />
    </IconShell>
  );
}

export function ChevronIcon(props: IconProps) {
  return (
    <IconShell {...props}>
      <path d="m14 6-6 6 6 6" />
    </IconShell>
  );
}

export function SunIcon(props: IconProps) {
  return (
    <IconShell {...props}>
      <path d="M12 8a4 4 0 1 0 0 8 4 4 0 0 0 0-8Z" />
      <path d="M12 2v2" />
      <path d="M12 20v2" />
      <path d="m4.93 4.93 1.41 1.41" />
      <path d="m17.66 17.66 1.41 1.41" />
      <path d="M2 12h2" />
      <path d="M20 12h2" />
      <path d="m6.34 17.66-1.41 1.41" />
      <path d="m19.07 4.93-1.41 1.41" />
    </IconShell>
  );
}

export function MoonIcon(props: IconProps) {
  return (
    <IconShell {...props}>
      <path d="M20 14.6A8 8 0 0 1 9.4 4a8.2 8.2 0 1 0 10.6 10.6Z" />
    </IconShell>
  );
}
