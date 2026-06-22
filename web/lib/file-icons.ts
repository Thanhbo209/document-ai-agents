/**
 * File icon helpers.
 * Maps filenames or extensions to icon paths in /public/file-icons/.
 * Graceful fallback to the generic "file" icon.
 */

const ICON_MAP: Record<string, string> = {
  pdf: "/file-icons/pdf.svg",
  txt: "/file-icons/txt.svg",
  text: "/file-icons/txt.svg",
  md: "/file-icons/md.svg",
  markdown: "/file-icons/md.svg",
  doc: "/file-icons/doc.svg",
  docx: "/file-icons/docx.svg",
  ppt: "/file-icons/ppt.svg",
  pptx: "/file-icons/pptx.svg",
  csv: "/file-icons/csv.svg",
  xls: "/file-icons/xls.svg",
  xlsx: "/file-icons/xlsx.svg",
  zip: "/file-icons/zip.svg",
  repo: "/file-icons/repo.svg",
  repository: "/file-icons/repo.svg",
  png: "/file-icons/png.svg",
  jpg: "/file-icons/jpg.svg",
  jpeg: "/file-icons/jpeg.svg",
  tiff: "/file-icons/tiff.svg",
  tif: "/file-icons/tif.svg",
  bmp: "/file-icons/bmp.svg",
  image: "/file-icons/image.svg",
  ocr: "/file-icons/image.svg",
  ocr_pdf: "/file-icons/pdf.svg",
  mp3: "/file-icons/mp3.svg",
  wav: "/file-icons/wav.svg",
  m4a: "/file-icons/m4a.svg",
  flac: "/file-icons/flac.svg",
  ogg: "/file-icons/ogg.svg",
  audio: "/file-icons/audio.svg",
  mp4: "/file-icons/mp4.svg",
  mov: "/file-icons/mov.svg",
  mkv: "/file-icons/mkv.svg",
  webm: "/file-icons/webm.svg",
  video: "/file-icons/video.svg",
  web: "/file-icons/web.svg",
  url: "/file-icons/web.svg",
  youtube: "/file-icons/youtube.svg",
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
  const ext = normalizeFileType(
    getFileExtension(filenameOrType) || filenameOrType,
  );
  return ICON_MAP[ext] ?? "/file-icons/file.svg";
}

/**
 * Returns a human-readable label for a file extension.
 */
export function getFileTypeLabel(filenameOrType: string): string {
  const ext = normalizeFileType(
    getFileExtension(filenameOrType) || filenameOrType,
  );
  const labels: Record<string, string> = {
    pdf: "PDF",
    txt: "Text",
    text: "Text",
    md: "Markdown",
    markdown: "Markdown",
    doc: "Word",
    docx: "Word",
    ppt: "PowerPoint",
    pptx: "PowerPoint",
    csv: "CSV",
    xls: "Excel",
    xlsx: "Excel",
    zip: "Repository ZIP",
    repo: "Repository",
    repository: "Repository",
    png: "PNG image",
    jpg: "JPEG image",
    jpeg: "JPEG image",
    tiff: "TIFF image",
    tif: "TIFF image",
    bmp: "Bitmap image",
    image: "Image",
    ocr: "OCR image",
    ocr_pdf: "OCR PDF",
    mp3: "MP3 audio",
    wav: "WAV audio",
    m4a: "M4A audio",
    flac: "FLAC audio",
    ogg: "OGG audio",
    audio: "Audio",
    mp4: "MP4 video",
    mov: "MOV video",
    mkv: "MKV video",
    webm: "WebM video",
    video: "Video",
    web: "Web page",
    url: "Web page",
    youtube: "YouTube",
  };
  return (labels[ext] ?? ext.toUpperCase()) || "File";
}

function normalizeFileType(value: string): string {
  return value.trim().replace(/^\./, "").toLowerCase();
}
