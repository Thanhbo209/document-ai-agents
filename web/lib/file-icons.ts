/**
 * File icon helpers.
 * Maps filenames or extensions to icon paths in /public/file-icons/.
 * Graceful fallback to the generic "file" icon.
 */

const ICON_MAP: Record<string, string> = {
  pdf: "/file-icons/pdf.svg",
  txt: "/file-icons/txt.svg",
  md: "/file-icons/md.svg",
  markdown: "/file-icons/md.svg",
};

/**
 * Extracts the lowercase file extension from a filename.
 * Returns empty string if no extension found.
 */
export function getFileExtension(filename: string): string {
  const dotIndex = filename.lastIndexOf(".");
  if (dotIndex === -1 || dotIndex === filename.length - 1) {
    return "";
  }
  return filename.slice(dotIndex + 1).toLowerCase();
}

/**
 * Returns the path to the appropriate file icon SVG.
 * Falls back to the generic file icon if the type is not recognised.
 */
export function getFileIconPath(filenameOrType: string): string {
  const ext = getFileExtension(filenameOrType) || filenameOrType.toLowerCase();
  return ICON_MAP[ext] ?? "/file-icons/file.svg";
}

/**
 * Returns a human-readable label for a file extension.
 */
export function getFileTypeLabel(filenameOrType: string): string {
  const ext = getFileExtension(filenameOrType) || filenameOrType.toLowerCase();
  const labels: Record<string, string> = {
    pdf: "PDF",
    txt: "Text",
    md: "Markdown",
    markdown: "Markdown",
  };
  return (labels[ext] ?? ext.toUpperCase()) || "File";
}
