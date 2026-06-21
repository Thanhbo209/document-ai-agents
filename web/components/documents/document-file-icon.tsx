import Image from "next/image";
import { getFileIconPath, getFileExtension } from "../../lib/file-icons";

type DocumentFileIconProps = {
  filename: string;
  size?: number;
  className?: string;
};

/**
 * Renders the correct file type icon for a given filename.
 * Gracefully falls back to an inline SVG badge if the icon image fails to load.
 */
export function DocumentFileIcon({
  filename,
  size = 40,
  className = "",
}: DocumentFileIconProps) {
  const iconPath = getFileIconPath(filename);
  const ext = getFileExtension(filename) || filename.toLowerCase();

  return (
    <div
      className={`shrink-0 overflow-hidden rounded-xl ${className}`}
      style={{ width: size, height: size }}
    >
      <Image
        src={iconPath}
        alt={`${ext.toUpperCase()} file`}
        width={size}
        height={size}
        className="h-full w-full object-contain"
        onError={(e) => {
          // Fallback: hide the broken image — the parent shows a text badge
          (e.target as HTMLImageElement).style.display = "none";
        }}
      />
    </div>
  );
}

/**
 * Inline SVG fallback badge when no icon image is available.
 */
export function FileTypeBadge({
  ext,
  size = 40,
}: {
  ext: string;
  size?: number;
}) {
  const colors: Record<string, { bg: string; text: string; border: string }> = {
    pdf: { bg: "#FEE2E2", text: "#DC2626", border: "#FCA5A5" },
    txt: { bg: "#EDE9FE", text: "#7C3AED", border: "#C4B5FD" },
    md: { bg: "#D1FAE5", text: "#059669", border: "#6EE7B7" },
    markdown: { bg: "#D1FAE5", text: "#059669", border: "#6EE7B7" },
  };

  const color = colors[ext.toLowerCase()] ?? {
    bg: "#F1F5F9",
    text: "#475569",
    border: "#CBD5E1",
  };

  const label = ext.toUpperCase().slice(0, 3);

  return (
    <div
      className="flex shrink-0 items-center justify-center rounded-xl text-xs font-bold"
      style={{
        width: size,
        height: size,
        backgroundColor: color.bg,
        color: color.text,
        border: `1px solid ${color.border}`,
      }}
      aria-label={`${label} file`}
    >
      {label}
    </div>
  );
}
