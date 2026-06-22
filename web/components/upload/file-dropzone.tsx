"use client";

import Image from "next/image";
import { useRef, useState } from "react";
import upload from "../../public/file-icons/upload.svg";
type FileDropzoneProps = {
  accept: string;
  title: string;
  description: string;
  hint: string;
  isBusy?: boolean;
  onFileSelected: (file: File) => void;
};

export function FileDropzone({
  accept,
  title,
  description,
  hint,
  isBusy = false,
  onFileSelected,
}: FileDropzoneProps) {
  const inputRef = useRef<HTMLInputElement | null>(null);
  const [isDragging, setIsDragging] = useState(false);

  function handleFiles(files: FileList | null) {
    const file = files?.[0];
    if (!file) return;
    onFileSelected(file);
    if (inputRef.current) {
      inputRef.current.value = "";
    }
  }

  return (
    <div
      role="button"
      tabIndex={0}
      aria-disabled={isBusy}
      onClick={() => {
        if (!isBusy) inputRef.current?.click();
      }}
      onKeyDown={(event) => {
        if (!isBusy && (event.key === "Enter" || event.key === " ")) {
          event.preventDefault();
          inputRef.current?.click();
        }
      }}
      onDragOver={(event) => {
        event.preventDefault();
        if (!isBusy) setIsDragging(true);
      }}
      onDragLeave={() => setIsDragging(false)}
      onDrop={(event) => {
        event.preventDefault();
        setIsDragging(false);
        if (!isBusy) {
          handleFiles(event.dataTransfer.files);
        }
      }}
      className={[
        "flex cursor-pointer flex-col items-center justify-center rounded-2xl border border-dashed px-6 py-10 text-center transition duration-200",
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
        isDragging
          ? "border-primary bg-accent"
          : "border-border bg-muted/55 hover:-translate-y-0.5 hover:bg-accent",
        isBusy ? "pointer-events-none opacity-70" : "",
      ].join(" ")}
    >
      <input
        ref={inputRef}
        type="file"
        accept={accept}
        className="hidden"
        onChange={(event) => handleFiles(event.target.files)}
      />

      <div className="mb-5 grid h-14 w-14 place-items-center rounded-2xl text-sm font-bold text-primary-foreground shadow-sm">
        <Image src={upload} width={500} height={500} alt="Upload Image" />
      </div>

      <p className="text-lg font-semibold text-card-foreground">{title}</p>
      <p className="mt-2 max-w-2xl text-sm leading-6 text-muted-foreground">
        {description}
      </p>
      <p className="mt-4 rounded-xl bg-background px-3 py-2 text-xs font-medium text-muted-foreground ring-1 ring-border">
        {hint}
      </p>
    </div>
  );
}
