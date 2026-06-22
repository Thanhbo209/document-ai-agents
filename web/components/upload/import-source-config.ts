import { ImportSourceOption } from "./import-source-selector";

export type FileSourceId = "documents" | "tables" | "images" | "media" | "repo";
export type UrlSourceId = "web" | "youtube";
export type SourceId = FileSourceId | UrlSourceId;

export type FileSourceConfig = {
  title: string;
  description: string;
  hint: string;
  accept: string;
  extensions: string[];
  processingMessage: string;
};

export const SOURCE_OPTIONS: ImportSourceOption[] = [
  {
    id: "documents",
    label: "Documents",
    description: "PDF, text, Markdown, Word, and presentation files.",
    iconType: "docx",
    detail: "File upload",
  },
  {
    id: "tables",
    label: "Tables",
    description: "CSV files and Excel workbooks with row-aware metadata.",
    iconType: "xlsx",
    detail: "File upload",
  },
  {
    id: "images",
    label: "Images with OCR",
    description: "Scanned images are processed with OCR when available.",
    iconType: "image",
    detail: "File upload",
  },
  {
    id: "media",
    label: "Audio and video",
    description: "Media files become timestamped transcript chunks.",
    iconType: "video",
    detail: "Async import",
  },
  {
    id: "web",
    label: "Web page",
    description: "Fetch a safe HTTPS page through the connector endpoint.",
    iconType: "web",
    detail: "Connector",
  },
  {
    id: "youtube",
    label: "YouTube transcript",
    description: "Import available transcript text with timestamps.",
    iconType: "youtube",
    detail: "Connector",
  },
  {
    id: "repo",
    label: "Repository ZIP",
    description: "Upload a safe ZIP archive; Git URLs are not supported yet.",
    iconType: "zip",
    detail: "File upload",
  },
];

export const FILE_SOURCE_CONFIG: Record<FileSourceId, FileSourceConfig> = {
  documents: {
    title: "Drop a document here, or click to upload",
    description:
      "Use this for policies, contracts, briefs, PDFs, Word docs, Markdown, text files, and slide decks.",
    hint: "Accepted: .pdf, .txt, .md, .markdown, .docx, .pptx",
    accept: ".pdf,.txt,.md,.markdown,.docx,.pptx",
    extensions: [".pdf", ".txt", ".md", ".markdown", ".docx", ".pptx"],
    processingMessage: "The document is being extracted and indexed.",
  },
  tables: {
    title: "Drop a spreadsheet or CSV here",
    description:
      "Tables are split into row-range blocks so citations can reference sheets and rows.",
    hint: "Accepted: .csv, .xlsx",
    accept: ".csv,.xlsx",
    extensions: [".csv", ".xlsx"],
    processingMessage: "The table is being profiled, chunked, and indexed.",
  },
  images: {
    title: "Drop a scanned image here",
    description:
      "OCR extracts searchable text and keeps confidence metadata for later review.",
    hint: "Accepted: .png, .jpg, .jpeg, .tiff, .tif, .bmp",
    accept: ".png,.jpg,.jpeg,.tiff,.tif,.bmp",
    extensions: [".png", ".jpg", ".jpeg", ".tiff", ".tif", ".bmp"],
    processingMessage: "The image is being processed with OCR.",
  },
  media: {
    title: "Drop audio or video here",
    description:
      "Large media runs in the background and becomes timestamped transcript chunks.",
    hint: "Accepted: .mp3, .wav, .m4a, .flac, .ogg, .mp4, .mov, .mkv, .webm",
    accept: ".mp3,.wav,.m4a,.flac,.ogg,.mp4,.mov,.mkv,.webm",
    extensions: [
      ".mp3",
      ".wav",
      ".m4a",
      ".flac",
      ".ogg",
      ".mp4",
      ".mov",
      ".mkv",
      ".webm",
    ],
    processingMessage:
      "The media file is queued for transcription. This can take a few minutes.",
  },
  repo: {
    title: "Drop a repository ZIP here",
    description:
      "Repository ingestion reads safe source files from a ZIP archive and preserves file and line metadata.",
    hint: "Accepted: .zip only. Repository URLs are not supported in this phase.",
    accept: ".zip",
    extensions: [".zip"],
    processingMessage: "The repository archive is being filtered and indexed.",
  },
};

export function isFileSource(sourceId: SourceId): sourceId is FileSourceId {
  return ["documents", "tables", "images", "media", "repo"].includes(sourceId);
}
