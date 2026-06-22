import {
  stripCitationMarkers,
  formatCitationLabel,
  formatCitationDetail,
} from "../../lib/citations";
import { QueryCitation, QuerySource } from "../../lib/chat-api";
import { StatusBadge } from "../ui/status-badge";
import { AttachedDocumentChips } from "./attached-document-chips";
import { WorkspaceDocument } from "../../lib/upload-api";

type ChatMessageProps = {
  role: "user" | "assistant";
  content: string;
  citations?: QueryCitation[];
  sources?: QuerySource[];
  confidence?: number;
  reviewFlags?: string[];
  isFinal?: boolean;
  attachedDocuments?: WorkspaceDocument[];
  messageId: string;
  sourceById: Map<string, QuerySource>;
  onOpenSource: (source: QuerySource) => void;
};

/**
 * Individual chat message bubble.
 *
 * For assistant messages:
 * - Strips [S1], [S2] citation markers from displayed text.
 * - Shows clean "Source 1", "Source 2" citation chips instead.
 * - Source drawer is still accessible via chip clicks.
 * - Backend data is NOT mutated — only display is transformed.
 */
export function ChatMessage({
  role,
  content,
  citations,
  confidence,
  reviewFlags,
  isFinal = false,
  attachedDocuments = [],
  messageId,
  sourceById,
  onOpenSource,
}: ChatMessageProps) {
  const displayContent =
    role === "assistant" ? stripCitationMarkers(content) : content;

  return (
    <article
      className={[
        "rounded-3xl p-5 shadow-sm",
        role === "user"
          ? "ml-auto max-w-2xl bg-primary text-primary-foreground"
          : "mr-auto max-w-3xl bg-card text-card-foreground ring-1 ring-border",
      ].join(" ")}
    >
      <p className="whitespace-pre-wrap leading-7">
        {displayContent || (role === "assistant" ? "" : "")}
      </p>

      {role === "user" && attachedDocuments.length > 0 && (
        <div className="mt-4 border-t border-primary-foreground/25 pt-3">
          <p className="mb-2 text-xs font-medium opacity-80">
            Attached context
          </p>
          <AttachedDocumentChips documents={attachedDocuments} compact />
        </div>
      )}

      {role === "assistant" && (
        <AssistantFooter
          messageId={messageId}
          citations={citations}
          confidence={confidence}
          reviewFlags={reviewFlags}
          isFinal={isFinal}
          sourceById={sourceById}
          onOpenSource={onOpenSource}
        />
      )}
    </article>
  );
}

function AssistantFooter({
  messageId,
  citations,
  confidence,
  reviewFlags,
  isFinal,
  sourceById,
  onOpenSource,
}: {
  messageId: string;
  citations?: QueryCitation[];
  confidence?: number;
  reviewFlags?: string[];
  isFinal: boolean;
  sourceById: Map<string, QuerySource>;
  onOpenSource: (source: QuerySource) => void;
}) {
  const hasCitations = citations && citations.length > 0;
  const hasConfidence = confidence !== undefined;
  const hasFlags = reviewFlags && reviewFlags.length > 0;

  if (!hasCitations && !hasConfidence && !hasFlags && !isFinal) {
    return null;
  }

  return (
    <div className="mt-4 border-t border-border pt-4">
      {/* Confidence + review flags */}
      {(hasConfidence || hasFlags) && (
        <div className="flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
          {hasConfidence && confidence !== undefined && (
            <span>
              Confidence: {(confidence * 100).toFixed(0)}%
            </span>
          )}
          {reviewFlags?.map((flag) => (
            <StatusBadge key={flag} status={flag} />
          ))}
        </div>
      )}

      {/* Citation chips — show "Source 1" not "[S1]" */}
      {hasCitations && (
        <div className="mt-3 flex flex-wrap gap-2">
          {citations!.map((citation) => {
            const source = sourceById.get(citation.source_id);
            const label = formatCitationLabel(citation.source_id);
            const detail = source
              ? formatCitationDetail(source.metadata, citation.source_page)
              : citation.source_page
                ? `Page ${citation.source_page}`
                : null;
            return (
              <button
                key={`${messageId}-${citation.source_id}`}
                type="button"
                disabled={!source}
                onClick={() => {
                  if (source) {
                    onOpenSource(source);
                  }
                }}
                className="rounded-xl border border-border bg-background px-3 py-1.5 text-xs font-medium text-muted-foreground transition hover:-translate-y-0.5 hover:bg-accent hover:text-accent-foreground disabled:opacity-50"
                title={
                  [
                    label,
                    detail,
                  ]
                    .filter(Boolean)
                    .join(" · ")
                }
              >
                {label}
                {detail ? (
                  <span className="text-muted-foreground"> · {detail}</span>
                ) : null}
              </button>
            );
          })}
        </div>
      )}

      {isFinal && !hasCitations && (
        <p className="mt-3 rounded-xl bg-muted px-3 py-2 text-xs text-muted-foreground">
          No source citations were returned for this answer.
        </p>
      )}
    </div>
  );
}
