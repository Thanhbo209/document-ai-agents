"use client";

import { Button } from "../ui/button";
import { StatusBadge } from "../ui/status-badge";

export type ImportStatus = "idle" | "uploading" | "processing" | "completed" | "failed";

type ImportStatusCardProps = {
  status: ImportStatus;
  title: string;
  message: string;
  chunksCreated?: number;
  canRetry?: boolean;
  workspaceId: string;
  onRetry?: () => void;
  onReset?: () => void;
};

export function ImportStatusCard({
  status,
  title,
  message,
  chunksCreated,
  canRetry = false,
  workspaceId,
  onRetry,
  onReset,
}: ImportStatusCardProps) {
  if (status === "idle") {
    return null;
  }

  const isSuccess = status === "completed";
  const isFailed = status === "failed";

  return (
    <div
      className={[
        "rounded-2xl border p-4",
        isFailed
          ? "border-destructive/30 bg-destructive/10"
          : "border-border bg-background/70",
      ].join(" ")}
    >
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <div className="flex flex-wrap items-center gap-2">
            <StatusBadge status={status} />
            {chunksCreated !== undefined && chunksCreated > 0 && (
              <span className="text-xs font-medium text-muted-foreground">
                {chunksCreated.toLocaleString()}{" "}
                {chunksCreated === 1 ? "chunk" : "chunks"} indexed
              </span>
            )}
          </div>
          <h4 className="mt-3 text-sm font-semibold text-card-foreground">
            {title}
          </h4>
          <p className="mt-1 text-sm leading-6 text-muted-foreground">
            {message}
          </p>
        </div>

        <div className="flex shrink-0 flex-wrap gap-2">
          {isSuccess && (
            <Button href={`/chat/${workspaceId}`} className="text-xs">
              Start chatting
            </Button>
          )}
          {isSuccess && onReset && (
            <Button variant="secondary" onClick={onReset} className="text-xs">
              Import another
            </Button>
          )}
          {canRetry && onRetry && (
            <Button variant="secondary" onClick={onRetry} className="text-xs">
              Retry
            </Button>
          )}
        </div>
      </div>
    </div>
  );
}
