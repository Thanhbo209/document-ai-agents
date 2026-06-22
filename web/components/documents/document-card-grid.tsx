import { WorkspaceDocument } from "../../lib/upload-api";
import { DocumentCard } from "./document-card";
import { EmptyState } from "../ui/empty-state";
import { LoadingState } from "../ui/loading-state";
import { ErrorState } from "../ui/error-state";
import { Button } from "../ui/button";

type DocumentCardGridProps = {
  documents: WorkspaceDocument[];
  workspaceId: string;
  isLoading?: boolean;
  errorMessage?: string | null;
  onRetry?: () => void;
};

/**
 * Responsive card grid: 1 col (mobile) → 2 col (tablet) → 3 col (desktop).
 */
export function DocumentCardGrid({
  documents,
  workspaceId,
  isLoading = false,
  errorMessage = null,
  onRetry,
}: DocumentCardGridProps) {
  if (isLoading) {
    return <LoadingState title="Loading documents" rows={3} />;
  }

  if (errorMessage) {
    return (
      <ErrorState
        message={errorMessage}
        action={
          onRetry ? (
            <Button onClick={onRetry} variant="secondary">
              Try again
            </Button>
          ) : undefined
        }
      />
    );
  }

  if (documents.length === 0) {
    return (
      <EmptyState
        title="No documents found"
        description="Import a file, web page, YouTube transcript, or repository ZIP to get started."
        icon={
          <svg
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.6"
            strokeLinecap="round"
            strokeLinejoin="round"
            className="h-7 w-7"
            aria-hidden="true"
          >
            <path d="M7 3.5h7l3 3V20a1 1 0 0 1-1 1H7a1 1 0 0 1-1-1V4.5a1 1 0 0 1 1-1Z" />
            <path d="M14 3.5V7h3" />
            <path d="M9 12h6" />
            <path d="M9 16h4" />
          </svg>
        }
      />
    );
  }

  return (
    <div className="grid gap-5 sm:grid-cols-2 xl:grid-cols-3">
      {documents.map((document) => (
        <DocumentCard
          key={document.id}
          document={document}
          workspaceId={workspaceId}
        />
      ))}
    </div>
  );
}
