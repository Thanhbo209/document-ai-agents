"use client";

import { useState } from "react";
import {
  ConnectorSourceType,
  ingestConnector,
  listDocuments,
  uploadDocument,
  WorkspaceDocument,
} from "../../lib/upload-api";
import {
  FILE_SOURCE_CONFIG,
  FileSourceId,
  isFileSource,
  SOURCE_OPTIONS,
  SourceId,
} from "./import-source-config";
import { FileDropzone } from "./file-dropzone";
import { ImportSourceSelector } from "./import-source-selector";
import { ImportStatus, ImportStatusCard } from "./import-status-card";
import { UrlImportForm } from "./url-import-form";

type UploadDropzoneProps = {
  workspaceId: string;
  onUploaded: () => void;
};

type LastAttempt =
  | { kind: "file"; sourceId: FileSourceId; file: File }
  | { kind: "connector"; sourceType: ConnectorSourceType; url: string };

const POLL_INTERVAL_MS = 2500;
const POLL_ATTEMPTS = 24;

export function UploadDropzone({
  workspaceId,
  onUploaded,
}: UploadDropzoneProps) {
  const [selectedSource, setSelectedSource] = useState<SourceId>("documents");
  const [status, setStatus] = useState<ImportStatus>("idle");
  const [statusTitle, setStatusTitle] = useState("");
  const [statusMessage, setStatusMessage] = useState("");
  const [chunksCreated, setChunksCreated] = useState<number | undefined>();
  const [lastAttempt, setLastAttempt] = useState<LastAttempt | null>(null);
  const [webUrl, setWebUrl] = useState("");
  const [youtubeUrl, setYoutubeUrl] = useState("");
  const [isPolling, setIsPolling] = useState(false);

  const isBusy = status === "uploading" || isPolling;
  const fileConfig = isFileSource(selectedSource)
    ? FILE_SOURCE_CONFIG[selectedSource]
    : null;

  async function handleFileImport(file: File, sourceId: FileSourceId) {
    const config = FILE_SOURCE_CONFIG[sourceId];
    const extension = getFileExtension(file.name);

    setLastAttempt({ kind: "file", sourceId, file });
    setChunksCreated(undefined);

    if (file.size === 0) {
      showFailure("Empty file", "Choose a file that contains content.");
      return;
    }

    if (!config.extensions.includes(extension)) {
      showFailure(
        "Unsupported file for this source",
        `Choose one of: ${config.extensions.join(", ")}.`,
      );
      return;
    }

    setStatus("uploading");
    setStatusTitle(`Uploading ${file.name}`);
    setStatusMessage(config.processingMessage);

    try {
      const result = await uploadDocument(workspaceId, file);
      onUploaded();

      if (isProcessingStatus(result.status)) {
        setStatus("processing");
        setStatusTitle(`${file.name} is processing`);
        setStatusMessage(
          "The upload succeeded. Processing is running in the background, and this panel will watch the existing document list for completion.",
        );
        await pollDocumentUntilReady(result.document_id, file.name);
        return;
      }

      setChunksCreated(result.chunks_created);
      setStatus("completed");
      setStatusTitle(`${file.name} imported`);
      setStatusMessage(successMessage(result.chunks_created));
    } catch (error) {
      showFailure(
        "Import failed",
        error instanceof Error ? error.message : "The file could not be imported.",
      );
    }
  }

  async function handleConnectorImport(sourceType: ConnectorSourceType, url: string) {
    const trimmedUrl = url.trim();
    const label = sourceType === "web" ? "web page" : "YouTube transcript";

    setLastAttempt({ kind: "connector", sourceType, url: trimmedUrl });
    setChunksCreated(undefined);

    const validationMessage = validateConnectorUrl(sourceType, trimmedUrl);
    if (validationMessage) {
      showFailure("Invalid URL", validationMessage);
      return;
    }

    setStatus("uploading");
    setStatusTitle(`Importing ${label}`);
    setStatusMessage("The connector is fetching content and preparing chunks.");

    try {
      const result = await ingestConnector(workspaceId, {
        source_type: sourceType,
        url: trimmedUrl,
      });
      onUploaded();
      setChunksCreated(result.chunks_created);
      setStatus(isProcessingStatus(result.status) ? "processing" : "completed");
      setStatusTitle(
        isProcessingStatus(result.status)
          ? `${label} is processing`
          : `${capitalize(label)} imported`,
      );
      setStatusMessage(
        isProcessingStatus(result.status)
          ? "Processing has started. Refresh the document list to watch progress."
          : successMessage(result.chunks_created),
      );
    } catch (error) {
      showFailure(
        "Connector import failed",
        error instanceof Error
          ? error.message
          : "The connector could not import this source.",
      );
    }
  }

  async function pollDocumentUntilReady(documentId: string, fallbackTitle: string) {
    setIsPolling(true);
    try {
      for (let attempt = 0; attempt < POLL_ATTEMPTS; attempt += 1) {
        await delay(POLL_INTERVAL_MS);
        const response = await listDocuments(workspaceId);
        const document = response.documents.find((item) => item.id === documentId);
        onUploaded();

        if (!document) {
          continue;
        }

        if (document.status === "failed" || document.latest_job?.status === "failed") {
          throw new Error(
            document.latest_job?.error_message ||
              "Processing failed. Check the document card for details.",
          );
        }

        if (
          document.status === "indexed" ||
          document.latest_job?.status === "succeeded"
        ) {
          setChunksCreated(document.chunk_count);
          setStatus("completed");
          setStatusTitle(`${document.title || fallbackTitle} imported`);
          setStatusMessage(successMessage(document.chunk_count));
          return;
        }

        setStatusMessage(statusMessageForDocument(document, fallbackTitle));
      }

      setStatus("processing");
      setStatusTitle(`${fallbackTitle} is still processing`);
      setStatusMessage(
        "Processing is still running. You can refresh the document library later to see the final status.",
      );
    } finally {
      setIsPolling(false);
    }
  }

  function retryLastAttempt() {
    if (!lastAttempt || isBusy) return;

    if (lastAttempt.kind === "file") {
      void handleFileImport(lastAttempt.file, lastAttempt.sourceId);
      return;
    }

    void handleConnectorImport(lastAttempt.sourceType, lastAttempt.url);
  }

  function showFailure(title: string, message: string) {
    setStatus("failed");
    setStatusTitle(title);
    setStatusMessage(message);
  }

  return (
    <section
      id="documents"
      className="overflow-hidden rounded-3xl bg-card shadow-sm ring-1 ring-border/70"
    >
      <div className="border-b border-border px-6 py-5">
        <p className="text-sm font-medium text-muted-foreground">
          Source intake
        </p>
        <h3 className="mt-1 text-xl font-semibold tracking-tight text-card-foreground">
          Import content into this workspace
        </h3>
        <p className="mt-2 max-w-3xl text-sm leading-6 text-muted-foreground">
          Choose the source type first so the importer can show the exact
          validation rules, processing behavior, and supported backend path.
        </p>
      </div>

      <div className="space-y-5 p-5">
        <ImportSourceSelector
          options={SOURCE_OPTIONS}
          selectedId={selectedSource}
          disabled={isBusy}
          onSelect={(id) => setSelectedSource(id as SourceId)}
        />

        {fileConfig && (
          <FileDropzone
            accept={fileConfig.accept}
            title={fileConfig.title}
            description={fileConfig.description}
            hint={fileConfig.hint}
            isBusy={isBusy}
            onFileSelected={(file) => void handleFileImport(file, selectedSource as FileSourceId)}
          />
        )}

        {selectedSource === "web" && (
          <UrlImportForm
            label="Web page URL"
            title="Import a web page"
            description="The backend fetches HTTPS pages through SSRF protections and extracts readable text."
            placeholder="https://example.com/policy"
            value={webUrl}
            isBusy={isBusy}
            submitLabel="Import page"
            helperText="Only public HTTPS pages are accepted by default. Localhost, private networks, and unsafe protocols are blocked server-side."
            onChange={setWebUrl}
            onSubmit={() => void handleConnectorImport("web", webUrl)}
          />
        )}

        {selectedSource === "youtube" && (
          <UrlImportForm
            label="YouTube URL"
            title="Import a YouTube transcript"
            description="The connector imports available transcript text and keeps timestamp metadata for citations."
            placeholder="https://www.youtube.com/watch?v=..."
            value={youtubeUrl}
            isBusy={isBusy}
            submitLabel="Import transcript"
            helperText="Only videos with an available transcript can be imported. Private videos and unavailable transcripts will fail with a backend error."
            onChange={setYoutubeUrl}
            onSubmit={() => void handleConnectorImport("youtube", youtubeUrl)}
          />
        )}

        <ImportStatusCard
          status={status}
          title={statusTitle}
          message={statusMessage}
          chunksCreated={chunksCreated}
          canRetry={status === "failed" && lastAttempt !== null}
          workspaceId={workspaceId}
          onRetry={retryLastAttempt}
          onReset={() => {
            setStatus("idle");
            setStatusTitle("");
            setStatusMessage("");
            setChunksCreated(undefined);
          }}
        />
      </div>
    </section>
  );
}

function getFileExtension(filename: string): string {
  const dotIndex = filename.lastIndexOf(".");
  if (dotIndex === -1) return "";
  return filename.slice(dotIndex).toLowerCase();
}

function isProcessingStatus(status: string): boolean {
  return ["created", "pending", "processing", "queued"].includes(
    status.toLowerCase(),
  );
}

function successMessage(chunksCreated: number): string {
  if (chunksCreated === 0) {
    return "The source was imported. Indexing reported no chunks, so try another source if chat cannot retrieve from it.";
  }
  return `${chunksCreated.toLocaleString()} ${
    chunksCreated === 1 ? "chunk is" : "chunks are"
  } indexed and ready for grounded chat.`;
}

function statusMessageForDocument(
  document: WorkspaceDocument,
  fallbackTitle: string,
): string {
  const title = document.title || fallbackTitle;
  const jobStatus = document.latest_job?.status ?? document.status;
  return `${title} is ${jobStatus}. Large media and OCR files can take longer to process.`;
}

function validateConnectorUrl(
  sourceType: ConnectorSourceType,
  value: string,
): string | null {
  if (!value) {
    return "Enter a URL before importing.";
  }

  let parsed: URL;
  try {
    parsed = new URL(value);
  } catch {
    return "Enter a valid URL.";
  }

  if (parsed.protocol !== "https:") {
    return "Use an HTTPS URL.";
  }

  if (sourceType === "youtube") {
    const host = parsed.hostname.toLowerCase();
    const isYouTubeHost =
      host === "youtu.be" ||
      host === "youtube.com" ||
      host.endsWith(".youtube.com");

    if (!isYouTubeHost) {
      return "Enter a YouTube URL.";
    }
  }

  return null;
}

function delay(ms: number): Promise<void> {
  return new Promise((resolve) => window.setTimeout(resolve, ms));
}

function capitalize(value: string): string {
  return value.charAt(0).toUpperCase() + value.slice(1);
}
