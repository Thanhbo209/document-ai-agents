"use client";

import { useRef, useState } from "react";
import { uploadDocument } from "../../lib/upload-api";
import { ErrorState } from "../ui/error-state";

type UploadDropzoneProps = {
  workspaceId: string;
  onUploaded: () => void;
};

export function UploadDropzone({
  workspaceId,
  onUploaded,
}: UploadDropzoneProps) {
  const inputRef = useRef<HTMLInputElement | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [isError, setIsError] = useState(false);

  async function handleFiles(files: FileList | null) {
    const file = files?.[0];

    if (!file) {
      return;
    }

    setIsUploading(true);
    setMessage(null);
    setIsError(false);

    try {
      const result = await uploadDocument(workspaceId, file);

      const chunkText =
        result.chunks_created === 1
          ? "1 chunk indexed"
          : `${result.chunks_created} chunks indexed`;
      setMessage(
        `Upload complete — ${chunkText} and ready for chat.`,
      );
      onUploaded();
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Upload failed.");
      setIsError(true);
    } finally {
      setIsUploading(false);
      if (inputRef.current) {
        inputRef.current.value = "";
      }
    }
  }

  return (
    <section
      id="documents"
      className="overflow-hidden rounded-3xl bg-card shadow-sm ring-1 ring-border/70"
    >
      <div className="border-b border-border px-6 py-5">
        <p className="text-sm font-medium text-muted-foreground">
          Document intake
        </p>
        <h3 className="mt-1 text-xl font-semibold tracking-tight text-card-foreground">
          Upload and process source files
        </h3>
      </div>
      <div
        role="button"
        tabIndex={0}
        onClick={() => inputRef.current?.click()}
        onKeyDown={(event) => {
          if (event.key === "Enter" || event.key === " ") {
            inputRef.current?.click();
          }
        }}
        onDragOver={(event) => {
          event.preventDefault();
          setIsDragging(true);
        }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={(event) => {
          event.preventDefault();
          setIsDragging(false);
          void handleFiles(event.dataTransfer.files);
        }}
        className={[
          "m-5 flex cursor-pointer flex-col items-center justify-center rounded-2xl border border-dashed px-6 py-12 text-center transition duration-200",
          "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
          isDragging
            ? "border-primary bg-accent"
            : "border-border bg-muted/55 hover:-translate-y-0.5 hover:bg-accent",
        ].join(" ")}
      >
        <input
          ref={inputRef}
          type="file"
          accept=".txt,.md,.markdown,.pdf"
          className="hidden"
          onChange={(event) => void handleFiles(event.target.files)}
        />

        <div className="mb-5 grid h-14 w-14 place-items-center rounded-2xl bg-primary text-primary-foreground shadow-sm">
          UP
        </div>

        <p className="text-lg font-semibold text-card-foreground">
          Drop a document here, or click to upload
        </p>

        <p className="mt-2 max-w-md text-sm leading-6 text-muted-foreground">
          Supported files: TXT, Markdown, PDF. Max size follows backend config.
        </p>

        {isUploading && (
          <p className="mt-4 text-sm font-medium text-card-foreground">
            Uploading and processing...
          </p>
        )}
      </div>

      {message && (
        <div className="px-5 pb-5">
          {isError ? (
            <ErrorState message={message} />
          ) : (
            <p className="rounded-2xl bg-accent px-4 py-3 text-sm font-medium text-accent-foreground">
              {message}
            </p>
          )}
        </div>
      )}
    </section>
  );
}
