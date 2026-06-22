import Image from "next/image";

import {
  getFileExtension,
  getFileIconPath,
  getFileTypeLabel,
} from "../../lib/file-icons";

type FileCardIconProps = {
  sourceType?: string;
  fileType?: string;
  size?: number;
  className?: string;
  showExtensionBadge?: boolean;
};

type DocumentFileIconProps = {
  filename: string;
  size?: number;
  className?: string;
};

/**
 * Consistent type-aware icon for document/file cards.
 *
 * The SVG is decorative; the nearby file title carries the accessible name.
 * `showExtensionBadge` is intentionally opt-in so file type text does not
 * become the main visual element again.
 */
export function FileCardIcon({
  sourceType,
  fileType,
  size = 40,
  className = "",
  showExtensionBadge = false,
}: FileCardIconProps) {
  const iconType = fileType ?? sourceType ?? "";
  const iconPath = getFileIconPath(iconType);
  const label = iconType ? getFileTypeLabel(iconType).slice(0, 4) : "";

  return (
    <span
      className={[
        "relative grid shrink-0 place-items-center rounded-xl ring-border",
        className,
      ].join(" ")}
      style={{ width: size, height: size }}
      aria-hidden="true"
    >
      <Image
        src={iconPath}
        alt=""
        width={size}
        height={size}
        className="h-[78%] w-[78%] object-contain"
        aria-hidden="true"
      />
      {showExtensionBadge && label && (
        <span className="absolute -bottom-1 -right-1 rounded-md border border-border bg-card px-1 py-0.5 text-[9px] font-semibold uppercase leading-none text-muted-foreground shadow-sm">
          {label}
        </span>
      )}
    </span>
  );
}

export function DocumentFileIcon({
  filename,
  size = 40,
  className = "",
}: DocumentFileIconProps) {
  return (
    <FileCardIcon
      fileType={getFileExtension(filename)}
      size={size}
      className={className}
    />
  );
}

export function FileTypeBadge({
  ext,
  size = 40,
  showExtensionBadge = false,
}: {
  ext: string;
  size?: number;
  showExtensionBadge?: boolean;
}) {
  return (
    <FileCardIcon
      sourceType={ext}
      size={size}
      showExtensionBadge={showExtensionBadge}
    />
  );
}
