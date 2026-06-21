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
import { ChatMessage } from "./chat-message";
import { ChatThinkingState } from "./chat-thinking-state";
import { TargetDocumentCard } from "./target-document-card";

type ChatPanelProps = {
  workspaceId: string;
};

type ChatMessageData = {
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
  const [messages, setMessages] = useState<ChatMessageData[]>([]);
  const [input, setInput] = useState("");
  const [isDocumentsLoading, setIsDocumentsLoading] = useState(true);
  const [isStreaming, setIsStreaming] = useState(false);
  const [selectedSource, setSelectedSource] = useState<QuerySource | null>(null);
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
    if (!trimmed || isStreaming) return;

    setErrorMessage(null);
    setInput("");

    const userMessage: ChatMessageData = {
      id: crypto.randomUUID(),
      role: "user",
      content: trimmed,
    };

    const assistantMessageId = crypto.randomUUID();
    const assistantMessage: ChatMessageData = {
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
              current.map((msg) =>
                msg.id === assistantMessageId
                  ? { ...msg, content: msg.content + text }
                  : msg,
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
      current.map((msg) =>
        msg.id === assistantMessageId
          ? {
              ...msg,
              id: response.assistant_message_id,
              content: response.message,
              citations: response.citations,
              sources: response.source_list,
              confidence: response.confidence,
              reviewFlags: response.review_flags,
            }
          : msg,
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
      description="Ask questions against your indexed documents and inspect cited sources."
      workspaceId={workspaceId}
    >
      <PageHeader
        kicker="Chat"
        title="Ask questions, get cited answers"
        description="Select specific documents to focus retrieval, or search your whole workspace. Answers include clickable source references."
      />

      <div className="grid gap-6 xl:grid-cols-[22rem_1fr]">
        {/* Retrieval scope sidebar */}
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
              : `Searching ${selectedCount} selected ${selectedCount === 1 ? "document" : "documents"}.`}
          </p>

          <div className="mt-5 space-y-2">
            {isDocumentsLoading ? (
              <LoadingState title="Loading documents" rows={3} />
            ) : documents.length === 0 ? (
              <EmptyState
                title="No documents indexed"
                description="Upload source files before starting a grounded chat."
                action={
                  <Button href={`/documents/${workspaceId}`}>
                    Upload documents
                  </Button>
                }
              />
            ) : (
              documents.map((document) => (
                <TargetDocumentCard
                  key={document.id}
                  document={document}
                  isSelected={selectedDocumentIds.includes(document.id)}
                  onToggle={() => toggleDocument(document.id)}
                />
              ))
            )}
          </div>
        </aside>

        {/* Conversation panel */}
        <section className="flex min-h-[calc(100dvh-12rem)] flex-col overflow-hidden rounded-3xl bg-card shadow-sm ring-1 ring-border/70">
          <div className="border-b border-border px-5 py-4">
            <p className="text-sm font-medium text-muted-foreground">
              Conversation
            </p>
            <h2 className="mt-1 text-xl font-semibold tracking-tight text-card-foreground">
              Chat session
            </h2>
          </div>

          <div className="flex-1 space-y-5 overflow-y-auto bg-muted/30 px-4 py-5 sm:px-6">
            {messages.length === 0 && !isStreaming && (
              <EmptyState
                title="Ask your first question"
                description="Try asking what a policy says, where a clause appears, or which source supports an answer."
                icon={
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" className="h-7 w-7" aria-hidden="true">
                    <path d="M5 6.5A3.5 3.5 0 0 1 8.5 3h7A3.5 3.5 0 0 1 19 6.5v4A3.5 3.5 0 0 1 15.5 14H11l-4.5 4v-4.5A3.5 3.5 0 0 1 5 10.5v-4Z" />
                  </svg>
                }
              />
            )}

            {messages.map((message) => (
              <ChatMessage
                key={message.id}
                messageId={message.id}
                role={message.role}
                content={message.content}
                citations={message.citations}
                sources={message.sources}
                confidence={message.confidence}
                reviewFlags={message.reviewFlags}
                sourceById={sourceById}
                onOpenSource={setSelectedSource}
              />
            ))}

            {/* Thinking state shown below last message while streaming */}
            <ChatThinkingState isThinking={isStreaming} />
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
                id="chat-input"
                value={input}
                onChange={(event) => setInput(event.target.value)}
                placeholder="Ask a question about your documents..."
                disabled={isStreaming}
                className="min-w-0 flex-1 rounded-2xl border border-input bg-background px-4 py-3 text-sm outline-none transition focus:ring-2 focus:ring-ring disabled:opacity-50"
                aria-label="Chat input"
              />

              <Button
                type="submit"
                disabled={isStreaming || !input.trim()}
                className="px-5"
              >
                {isStreaming ? "Sending\u2026" : "Ask"}
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
