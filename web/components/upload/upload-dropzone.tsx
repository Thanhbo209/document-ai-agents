"use client";

import { useRef, useState } from "react";
import { uploadDocument } from "../../lib/api";

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

  async function handleFiles(files: FileList | null) {
    const file = files?.[0];

    if (!file) {
      return;
    }

    setIsUploading(true);
    setMessage(null);

    try {
      const result = await uploadDocument(workspaceId, file);

      setMessage(
        `Uploaded successfully. Job ${result.job_id} created ${result.chunks_created} chunks.`,
      );
      onUploaded();
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Upload failed.");
    } finally {
      setIsUploading(false);
      if (inputRef.current) {
        inputRef.current.value = "";
      }
    }
  }

  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
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
          "flex cursor-pointer flex-col items-center justify-center rounded-xl border-2 border-dashed px-6 py-12 text-center transition",
          isDragging
            ? "border-slate-900 bg-slate-100"
            : "border-slate-300 bg-slate-50 hover:bg-slate-100",
        ].join(" ")}
      >
        <input
          ref={inputRef}
          type="file"
          accept=".txt,.md,.markdown,.pdf"
          className="hidden"
          onChange={(event) => void handleFiles(event.target.files)}
        />

        <p className="text-lg font-semibold text-slate-900">
          Drop a document here, or click to upload
        </p>

        <p className="mt-2 text-sm text-slate-500">
          Supported files: TXT, Markdown, PDF. Max size follows backend config.
        </p>

        {isUploading && (
          <p className="mt-4 text-sm font-medium text-slate-700">
            Uploading and processing...
          </p>
        )}
      </div>

      {message && (
        <p className="mt-4 rounded-lg bg-slate-100 px-4 py-3 text-sm text-slate-700">
          {message}
        </p>
      )}
    </section>
  );
}
