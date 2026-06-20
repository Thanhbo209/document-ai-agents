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
      const response = await listDocuments(workspaceId);
      setDocuments(response.documents);
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
    <div className="grid min-h-screen bg-slate-50 lg:grid-cols-[320px_1fr]">
      <aside className="border-r border-slate-200 bg-white p-5">
        <h1 className="text-xl font-bold text-slate-950">Chat</h1>
        <p className="mt-2 text-sm text-slate-500">
          Ask grounded questions over indexed workspace documents.
        </p>

        <div className="mt-6">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-semibold text-slate-900">
              Target files
            </h2>
            <button
              type="button"
              onClick={() => setSelectedDocumentIds([])}
              className="text-xs text-slate-500 hover:text-slate-900"
            >
              Clear
            </button>
          </div>

          <p className="mt-1 text-xs text-slate-500">
            {selectedCount === 0
              ? "Searching all documents."
              : `Searching ${selectedCount} selected document(s).`}
          </p>

          <div className="mt-4 space-y-2">
            {documents.map((document) => (
              <label
                key={document.id}
                className="flex cursor-pointer items-start gap-3 rounded-xl border border-slate-200 p-3 hover:bg-slate-50"
              >
                <input
                  type="checkbox"
                  checked={selectedDocumentIds.includes(document.id)}
                  onChange={() => toggleDocument(document.id)}
                  className="mt-1"
                />

                <span>
                  <span className="block text-sm font-medium text-slate-900">
                    {document.title}
                  </span>
                  <span className="mt-1 block text-xs text-slate-500">
                    {document.source_type} · {document.status} ·{" "}
                    {document.chunk_count} chunks
                  </span>
                </span>
              </label>
            ))}

            {documents.length === 0 && (
              <p className="rounded-xl bg-slate-50 p-3 text-sm text-slate-500">
                No documents yet. Upload documents first.
              </p>
            )}
          </div>
        </div>
      </aside>

      <main className="flex min-h-screen flex-col">
        <div className="border-b border-slate-200 bg-white px-6 py-4">
          <p className="font-mono text-xs text-slate-400">{workspaceId}</p>
          <h2 className="mt-1 text-lg font-semibold text-slate-950">
            Streaming grounded chat
          </h2>
        </div>

        <div className="flex-1 space-y-5 overflow-y-auto px-6 py-6">
          {messages.length === 0 && (
            <div className="rounded-2xl border border-dashed border-slate-300 bg-white p-8 text-center">
              <p className="text-lg font-semibold text-slate-900">
                Ask your first question
              </p>
              <p className="mt-2 text-sm text-slate-500">
                Example: “What is the refund policy?”
              </p>
            </div>
          )}

          {messages.map((message) => (
            <article
              key={message.id}
              className={[
                "rounded-2xl p-5 shadow-sm",
                message.role === "user"
                  ? "ml-auto max-w-2xl bg-slate-950 text-white"
                  : "mr-auto max-w-3xl border border-slate-200 bg-white text-slate-900",
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
          <div className="border-t border-red-200 bg-red-50 px-6 py-3 text-sm text-red-700">
            {errorMessage}
          </div>
        )}

        <form
          onSubmit={(event) => void handleSubmit(event)}
          className="border-t border-slate-200 bg-white p-4"
        >
          <div className="mx-auto flex max-w-4xl gap-3">
            <input
              value={input}
              onChange={(event) => setInput(event.target.value)}
              placeholder="Ask a question about your documents..."
              className="flex-1 rounded-xl border border-slate-300 px-4 py-3 text-sm outline-none ring-slate-900 focus:ring-2"
            />

            <button
              type="submit"
              disabled={isStreaming || !input.trim()}
              className="rounded-xl bg-slate-950 px-5 py-3 text-sm font-medium text-white disabled:cursor-not-allowed disabled:opacity-50"
            >
              {isStreaming ? "Streaming..." : "Ask"}
            </button>
          </div>
        </form>
      </main>

      <SourceDrawer
        source={selectedSource}
        onClose={() => setSelectedSource(null)}
      />
    </div>
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
    <div className="mt-4 border-t border-slate-100 pt-4">
      <div className="flex flex-wrap items-center gap-2 text-xs text-slate-500">
        {message.confidence !== undefined && (
          <span>Confidence: {message.confidence.toFixed(2)}</span>
        )}

        {message.reviewFlags?.map((flag) => (
          <span
            key={flag}
            className="rounded-full bg-amber-50 px-2 py-1 text-amber-700"
          >
            {flag}
          </span>
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
                className="rounded-full border border-slate-200 px-3 py-1 text-xs font-medium text-slate-700 hover:bg-slate-50 disabled:opacity-50"
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
