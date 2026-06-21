"use client";

import { useEffect, useMemo, useState } from "react";
import {
  QueryCitation,
  QueryResponse,
  QuerySource,
  streamWorkspaceQuery,
} from "../../lib/chat-api";
import { listDocuments, WorkspaceDocument } from "../../lib/upload-api";
import { SourceDrawer } from "../citations/source-drawer";
import { DashboardShell } from "../layout/dashboard-shell";
import { Button } from "../ui/button";
import { EmptyState } from "../ui/empty-state";
import { ErrorState } from "../ui/error-state";
import { LoadingState } from "../ui/loading-state";
import { PageHeader } from "../ui/page-header";
import { StatusBadge } from "../ui/status-badge";

type ChatPanelProps = {
  workspaceId: string;
};

type ChatMessage = {
  id: string;
  role: "user" | "assistant";
  content: string;
  citations?: QueryCitation[];
  sources?: QuerySource[];
  confidence?: number;
  reviewFlags?: string[];
};

export function ChatPanel({ workspaceId }: ChatPanelProps) {
  const [documents, setDocuments] = useState<WorkspaceDocument[]>([]);
  const [selectedDocumentIds, setSelectedDocumentIds] = useState<string[]>([]);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [isDocumentsLoading, setIsDocumentsLoading] = useState(true);
  const [isStreaming, setIsStreaming] = useState(false);
  const [selectedSource, setSelectedSource] = useState<QuerySource | null>(
    null,
  );
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const selectedCount = selectedDocumentIds.length;

  const sourceById = useMemo(() => {
    const map = new Map<string, QuerySource>();

    for (const message of messages) {
      for (const source of message.sources ?? []) {
        map.set(source.source_id, source);
      }
    }

    return map;
  }, [messages]);

  useEffect(() => {
    async function loadDocuments() {
      setIsDocumentsLoading(true);

      try {
        const response = await listDocuments(workspaceId);
        setDocuments(response.documents);
      } catch (error) {
        setErrorMessage(
          error instanceof Error ? error.message : "Could not load documents.",
        );
      } finally {
        setIsDocumentsLoading(false);
      }
    }

    void loadDocuments();
  }, [workspaceId]);

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();

    const trimmed = input.trim();

    if (!trimmed || isStreaming) {
      return;
    }

    setErrorMessage(null);
    setInput("");

    const userMessage: ChatMessage = {
      id: crypto.randomUUID(),
      role: "user",
      content: trimmed,
    };

    const assistantMessageId = crypto.randomUUID();
    const assistantMessage: ChatMessage = {
      id: assistantMessageId,
      role: "assistant",
      content: "",
      citations: [],
      sources: [],
    };

    setMessages((current) => [...current, userMessage, assistantMessage]);
    setIsStreaming(true);

    try {
      await streamWorkspaceQuery(
        workspaceId,
        {
          query: trimmed,
          document_ids:
            selectedDocumentIds.length > 0 ? selectedDocumentIds : undefined,
          top_k: 5,
        },
        {
          onToken: (text) => {
            setMessages((current) =>
              current.map((message) =>
                message.id === assistantMessageId
                  ? {
                      ...message,
                      content: message.content + text,
                    }
                  : message,
              ),
            );
          },
          onFinal: (response) => {
            applyFinalResponse(assistantMessageId, response);
          },
          onError: (message) => {
            setErrorMessage(message);
          },
        },
      );
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : "Query failed.");
    } finally {
      setIsStreaming(false);
    }
  }

  function applyFinalResponse(
    assistantMessageId: string,
    response: QueryResponse,
  ) {
    setMessages((current) =>
      current.map((message) =>
        message.id === assistantMessageId
          ? {
              ...message,
              id: response.assistant_message_id,
              content: response.message,
              citations: response.citations,
              sources: response.source_list,
              confidence: response.confidence,
              reviewFlags: response.review_flags,
            }
          : message,
      ),
    );
  }

  function toggleDocument(documentId: string) {
    setSelectedDocumentIds((current) =>
      current.includes(documentId)
        ? current.filter((id) => id !== documentId)
        : [...current, documentId],
    );
  }

  return (
    <DashboardShell
      activeItem="chat"
      title="Grounded chat"
      description="Ask questions against indexed workspace documents and inspect cited sources."
      workspaceId={workspaceId}
    >
      <PageHeader
        kicker="Chat"
        title="Ask questions with evidence in reach"
        description="Scope retrieval to selected documents or search the whole workspace. Streaming answers keep citations attached to the response."
        meta={
          <p className="font-mono text-xs text-muted-foreground">{workspaceId}</p>
        }
      />

      <div className="grid gap-6 xl:grid-cols-[22rem_1fr]">
        <aside className="rounded-3xl bg-card p-5 shadow-sm ring-1 ring-border/70">
          <div className="flex items-start justify-between gap-4">
            <div>
              <p className="text-sm font-medium text-muted-foreground">
                Retrieval scope
              </p>
              <h2 className="mt-1 text-xl font-semibold tracking-tight text-card-foreground">
                Target documents
              </h2>
            </div>
            <Button variant="quiet" onClick={() => setSelectedDocumentIds([])}>
              Clear
            </Button>
          </div>

          <p className="mt-3 text-sm leading-6 text-muted-foreground">
            {selectedCount === 0
              ? "Searching all indexed documents."
              : `Searching ${selectedCount} selected document(s).`}
          </p>

          <div className="mt-5 space-y-2">
            {isDocumentsLoading ? (
              <LoadingState title="Loading scope" rows={3} />
            ) : documents.length === 0 ? (
              <EmptyState
                title="No documents indexed"
                description="Upload source files before starting a grounded chat."
                action={
                  <Button href={`/workspaces/${workspaceId}#documents`}>
                    Upload documents
                  </Button>
                }
              />
            ) : (
              documents.map((document) => (
                <label
                  key={document.id}
                  className="group flex cursor-pointer items-start gap-3 rounded-2xl border border-border bg-background/70 p-3 transition duration-200 hover:-translate-y-0.5 hover:bg-accent"
                >
                  <input
                    type="checkbox"
                    checked={selectedDocumentIds.includes(document.id)}
                    onChange={() => toggleDocument(document.id)}
                    className="mt-1 accent-primary"
                  />

                  <span className="min-w-0">
                    <span className="block truncate text-sm font-medium text-card-foreground">
                      {document.title}
                    </span>
                    <span className="mt-2 flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
                      <StatusBadge status={document.status} />
                      <span>{document.source_type}</span>
                      <span>{document.chunk_count} chunks</span>
                    </span>
                  </span>
                </label>
              ))
            )}
          </div>
        </aside>

        <section className="flex min-h-[calc(100dvh-12rem)] flex-col overflow-hidden rounded-3xl bg-card shadow-sm ring-1 ring-border/70">
          <div className="border-b border-border px-5 py-4">
            <p className="text-sm font-medium text-muted-foreground">
              Streaming session
            </p>
            <h2 className="mt-1 text-xl font-semibold tracking-tight text-card-foreground">
              Conversation
            </h2>
          </div>

          <div className="flex-1 space-y-5 overflow-y-auto bg-muted/30 px-4 py-5 sm:px-6">
            {messages.length === 0 && (
              <EmptyState
                title="Ask your first question"
                description="Try asking what a policy says, where a clause appears, or which source supports an answer."
              />
            )}

            {messages.map((message) => (
              <article
                key={message.id}
                className={[
                  "rounded-3xl p-5 shadow-sm",
                  message.role === "user"
                    ? "ml-auto max-w-2xl bg-primary text-primary-foreground"
                    : "mr-auto max-w-3xl bg-card text-card-foreground ring-1 ring-border",
                ].join(" ")}
              >
                <p className="whitespace-pre-wrap leading-7">
                  {message.content || "Thinking..."}
                </p>

                {message.role === "assistant" && (
                  <AssistantMetadata
                    message={message}
                    sourceById={sourceById}
                    onOpenSource={setSelectedSource}
                  />
                )}
              </article>
            ))}
          </div>

          {errorMessage && (
            <div className="border-t border-border px-5 py-3">
              <ErrorState message={errorMessage} />
            </div>
          )}

          <form
            onSubmit={(event) => void handleSubmit(event)}
            className="border-t border-border bg-card p-4"
          >
            <div className="flex gap-3">
              <input
                value={input}
                onChange={(event) => setInput(event.target.value)}
                placeholder="Ask a question about your documents..."
                className="min-w-0 flex-1 rounded-2xl border border-input bg-background px-4 py-3 text-sm outline-none transition focus:ring-2 focus:ring-ring"
              />

              <Button
                type="submit"
                disabled={isStreaming || !input.trim()}
                className="px-5"
              >
                {isStreaming ? "Streaming" : "Ask"}
              </Button>
            </div>
          </form>
        </section>
      </div>

      <SourceDrawer
        source={selectedSource}
        onClose={() => setSelectedSource(null)}
      />
    </DashboardShell>
  );
}

function AssistantMetadata({
  message,
  sourceById,
  onOpenSource,
}: {
  message: ChatMessage;
  sourceById: Map<string, QuerySource>;
  onOpenSource: (source: QuerySource) => void;
}) {
  if (!message.citations?.length && message.confidence === undefined) {
    return null;
  }

  return (
    <div className="mt-4 border-t border-border pt-4">
      <div className="flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
        {message.confidence !== undefined && (
          <span>Confidence: {message.confidence.toFixed(2)}</span>
        )}

        {message.reviewFlags?.map((flag) => (
          <StatusBadge key={flag} status={flag} />
        ))}
      </div>

      {message.citations && message.citations.length > 0 && (
        <div className="mt-3 flex flex-wrap gap-2">
          {message.citations.map((citation) => {
            const source = sourceById.get(citation.source_id);

            return (
              <button
                key={`${message.id}-${citation.source_id}`}
                type="button"
                disabled={!source}
                onClick={() => {
                  if (source) {
                    onOpenSource(source);
                  }
                }}
                className="rounded-xl border border-border bg-background px-3 py-1.5 text-xs font-medium text-muted-foreground transition hover:-translate-y-0.5 hover:bg-accent hover:text-accent-foreground disabled:opacity-50"
              >
                {citation.source_id}
                {citation.source_page ? ` · page ${citation.source_page}` : ""}
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
}
