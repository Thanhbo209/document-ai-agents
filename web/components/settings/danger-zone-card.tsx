"use client";

import { useState } from "react";
import { Button } from "../ui/button";
import { SectionCard } from "../ui/section-card";

type DangerZoneCardProps = {
  workspaceStatus: string;
  isRequestingDeletion: boolean;
  reason: string;
  onReasonChange: (reason: string) => void;
  onConfirmDelete: () => void;
};

/**
 * Danger zone card with inline confirmation — replaces window.confirm().
 * Clearly explains this is a soft-delete, not permanent deletion.
 */
export function DangerZoneCard({
  workspaceStatus,
  isRequestingDeletion,
  reason,
  onReasonChange,
  onConfirmDelete,
}: DangerZoneCardProps) {
  const [isConfirming, setIsConfirming] = useState(false);
  const isActive = workspaceStatus === "active";

  return (
    <SectionCard className="ring-destructive/25">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <p className="text-sm font-semibold text-destructive">Danger zone</p>
          <h3 className="mt-1 text-2xl font-semibold tracking-tight text-card-foreground">
            Request workspace removal
          </h3>
        </div>
      </div>

      <p className="mt-3 max-w-2xl text-sm leading-6 text-muted-foreground">
        This action soft-disables the workspace. Normal operations such as
        uploads, queries, and chat will be disabled while the removal is
        pending. Your data is preserved and can be exported before permanent
        deletion is processed.
      </p>

      {/* Warning banner */}
      <div className="mt-5 flex items-start gap-3 rounded-2xl bg-destructive/8 px-4 py-3 ring-1 ring-destructive/20">
        <svg
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.8"
          strokeLinecap="round"
          strokeLinejoin="round"
          className="mt-0.5 h-5 w-5 shrink-0 text-destructive"
          aria-hidden="true"
        >
          <path d="M12 9v4" />
          <path d="M12 17h.01" />
          <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0Z" />
        </svg>
        <p className="text-sm text-destructive">
          This soft-disables the workspace. Permanent deletion is handled by a
          separate background process that is not yet implemented.
        </p>
      </div>

      {!isConfirming ? (
        <div className="mt-5">
          <Button
            variant="danger"
            disabled={!isActive || isRequestingDeletion}
            onClick={() => setIsConfirming(true)}
          >
            Request workspace removal
          </Button>
          {!isActive && (
            <p className="mt-2 text-xs text-muted-foreground">
              A removal request is already pending or the workspace is not active.
            </p>
          )}
        </div>
      ) : (
        <div className="mt-5 space-y-4">
          <p className="text-sm font-medium text-card-foreground">
            Are you sure you want to request removal of this workspace?
          </p>

          <textarea
            value={reason}
            onChange={(e) => onReasonChange(e.target.value)}
            placeholder="Optional: explain why you are removing this workspace"
            className="min-h-24 w-full rounded-2xl border border-input bg-background px-4 py-3 text-sm outline-none transition focus:ring-2 focus:ring-ring"
            aria-label="Deletion reason"
          />

          <div className="flex flex-wrap gap-2">
            <Button
              variant="danger"
              disabled={isRequestingDeletion}
              onClick={() => {
                setIsConfirming(false);
                onConfirmDelete();
              }}
            >
              {isRequestingDeletion ? "Submitting\u2026" : "Confirm removal request"}
            </Button>
            <Button
              variant="secondary"
              onClick={() => setIsConfirming(false)}
            >
              Cancel
            </Button>
          </div>
        </div>
      )}
    </SectionCard>
  );
}
