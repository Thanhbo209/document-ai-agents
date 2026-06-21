import { stripCitationMarkers, formatCitationLabel } from "../../lib/citations";
import { QueryCitation, QuerySource } from "../../lib/chat-api";
import { StatusBadge } from "../ui/status-badge";

type ChatMessageProps = {
  role: "user" | "assistant";
  content: string;
  citations?: QueryCitation[];
  sources?: QuerySource[];
  confidence?: number;
  reviewFlags?: string[];
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

      {role === "assistant" && (
        <AssistantFooter
          messageId={messageId}
          citations={citations}
          confidence={confidence}
          reviewFlags={reviewFlags}
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
  sourceById,
  onOpenSource,
}: {
  messageId: string;
  citations?: QueryCitation[];
  confidence?: number;
  reviewFlags?: string[];
  sourceById: Map<string, QuerySource>;
  onOpenSource: (source: QuerySource) => void;
}) {
  const hasCitations = citations && citations.length > 0;
  const hasConfidence = confidence !== undefined;
  const hasFlags = reviewFlags && reviewFlags.length > 0;

  if (!hasCitations && !hasConfidence && !hasFlags) {
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
                  citation.source_page
                    ? `${label} · page ${citation.source_page}`
                    : label
                }
              >
                {label}
                {citation.source_page ? ` · p.${citation.source_page}` : ""}
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
}
