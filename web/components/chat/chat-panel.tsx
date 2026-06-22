"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import {
  ChatHistoryMessage,
  ChatSession,
  createChatSession,
  listChatSessionMessages,
  listChatSessions,
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
import { AttachedDocumentChips } from "./attached-document-chips";
import { ChatMessage } from "./chat-message";
import { ChatSidebar } from "./chat-sidebar";
import { ChatThinkingState } from "./chat-thinking-state";
import { DocumentAttachModal } from "./document-attach-modal";

type ChatPanelProps = {
  workspaceId: string;
};

const MAX_QUESTION_LENGTH = 2000;

type ChatMessageData = {
  id: string;
  role: "user" | "assistant";
  content: string;
  citations?: QueryCitation[];
  sources?: QuerySource[];
  confidence?: number;
  reviewFlags?: string[];
  isFinal?: boolean;
  attachedDocumentIds?: string[];
};

type LastQuestion = {
  text: string;
  documentIds: string[];
};

export function ChatPanel({ workspaceId }: ChatPanelProps) {
  const [documents, setDocuments] = useState<WorkspaceDocument[]>([]);
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessageData[]>([]);
  const [selectedAttachmentIds, setSelectedAttachmentIds] = useState<string[]>([]);
  const [input, setInput] = useState("");
  const [isDocumentsLoading, setIsDocumentsLoading] = useState(true);
  const [isSessionsLoading, setIsSessionsLoading] = useState(true);
  const [isMessagesLoading, setIsMessagesLoading] = useState(false);
  const [isStreaming, setIsStreaming] = useState(false);
  const [isAttachModalOpen, setIsAttachModalOpen] = useState(false);
  const [selectedSource, setSelectedSource] = useState<QuerySource | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [sessionsError, setSessionsError] = useState<string | null>(null);
  const [lastQuestion, setLastQuestion] = useState<LastQuestion | null>(null);

  const documentById = useMemo(() => {
    const map = new Map<string, WorkspaceDocument>();
    for (const document of documents) {
      map.set(document.id, document);
    }
    return map;
  }, [documents]);

  const attachedDocuments = useMemo(
    () =>
      selectedAttachmentIds
        .map((id) => documentById.get(id))
        .filter((document): document is WorkspaceDocument => Boolean(document)),
    [documentById, selectedAttachmentIds],
  );

  const indexedDocuments = useMemo(
    () => documents.filter((document) => document.status === "indexed"),
    [documents],
  );

  const activeSession = sessions.find((session) => session.id === activeSessionId);

  const sourceById = useMemo(() => {
    const map = new Map<string, QuerySource>();
    for (const message of messages) {
      for (const source of message.sources ?? []) {
        map.set(source.source_id, source);
      }
    }
    return map;
  }, [messages]);

  const loadDocuments = useCallback(async () => {
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
  }, [workspaceId]);

  const loadSessions = useCallback(async () => {
    setIsSessionsLoading(true);
    setSessionsError(null);
    try {
      const response = await listChatSessions(workspaceId);
      setSessions(response);
      return response;
    } catch (error) {
      const message =
        error instanceof Error ? error.message : "Could not load chat sessions.";
      setSessionsError(message);
      return [];
    } finally {
      setIsSessionsLoading(false);
    }
  }, [workspaceId]);

  const loadMessages = useCallback(
    async (sessionId: string) => {
      setIsMessagesLoading(true);
      setErrorMessage(null);
      try {
        const response = await listChatSessionMessages(workspaceId, sessionId);
        setMessages(response.map(historyMessageToChatMessage));
        setSelectedAttachmentIds(lastAttachedDocumentIds(response));
      } catch (error) {
        setErrorMessage(
          error instanceof Error ? error.message : "Could not load messages.",
        );
      } finally {
        setIsMessagesLoading(false);
      }
    },
    [workspaceId],
  );

  useEffect(() => {
    void initializeChat();

    async function initializeChat() {
      const [loadedSessions] = await Promise.all([loadSessions(), loadDocuments()]);
      if (loadedSessions.length > 0) {
        const firstSession = loadedSessions[0];
        setActiveSessionId(firstSession.id);
        await loadMessages(firstSession.id);
      }
    }
  }, [loadDocuments, loadMessages, loadSessions]);

  async function handleNewChat() {
    try {
      setErrorMessage(null);
      const session = await createChatSession(workspaceId);
      setSessions((current) => [session, ...current]);
      setActiveSessionId(session.id);
      setMessages([]);
      setSelectedAttachmentIds([]);
      setSelectedSource(null);
    } catch (error) {
      setErrorMessage(
        error instanceof Error ? error.message : "Could not create chat.",
      );
    }
  }

  async function handleSelectSession(sessionId: string) {
    if (sessionId === activeSessionId || isStreaming) {
      return;
    }

    setActiveSessionId(sessionId);
    setSelectedSource(null);
    await loadMessages(sessionId);
  }

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await sendQuestion(input.trim());
  }

  async function sendQuestion(text: string, documentIds = selectedAttachmentIds) {
    if (!text || isStreaming) return;

    if (!isDocumentsLoading && documents.length === 0) {
      setErrorMessage("Import documents before asking grounded questions.");
      return;
    }

    if (!isDocumentsLoading && indexedDocuments.length === 0) {
      setErrorMessage("Your imported sources are still processing or failed.");
      return;
    }

    if (text.length > MAX_QUESTION_LENGTH) {
      setErrorMessage(
        `Keep questions under ${MAX_QUESTION_LENGTH.toLocaleString()} characters.`,
      );
      return;
    }

    const validDocumentIds = documentIds.filter((id) => {
      const document = documentById.get(id);
      return document?.status === "indexed" && document.chunk_count > 0;
    });

    if (validDocumentIds.length !== documentIds.length) {
      setSelectedAttachmentIds(validDocumentIds);
      setErrorMessage(
        "One or more attached documents are no longer ready for chat and were removed.",
      );
      return;
    }

    const session = await ensureActiveSession();
    const userMessage: ChatMessageData = {
      id: crypto.randomUUID(),
      role: "user",
      content: text,
      attachedDocumentIds: validDocumentIds,
    };
    const assistantMessageId = crypto.randomUUID();
    const assistantMessage: ChatMessageData = {
      id: assistantMessageId,
      role: "assistant",
      content: "",
      citations: [],
      sources: [],
      attachedDocumentIds: validDocumentIds,
      isFinal: false,
    };

    setErrorMessage(null);
    setInput("");
    setLastQuestion({ text, documentIds: validDocumentIds });
    setMessages((current) => [...current, userMessage, assistantMessage]);
    setIsStreaming(true);

    try {
      await streamWorkspaceQuery(
        workspaceId,
        {
          query: text,
          chat_session_id: session.id,
          document_ids:
            validDocumentIds.length > 0 ? validDocumentIds : undefined,
          top_k: 5,
        },
        {
          onToken: (token) => {
            setMessages((current) =>
              current.map((message) =>
                message.id === assistantMessageId
                  ? { ...message, content: message.content + token }
                  : message,
              ),
            );
          },
          onFinal: (response) => {
            applyFinalResponse(assistantMessageId, response, validDocumentIds);
            void loadSessions();
          },
          onError: (message) => {
            setErrorMessage(message);
            removeEmptyAssistantMessage(assistantMessageId);
          },
        },
      );
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : "Query failed.");
      removeEmptyAssistantMessage(assistantMessageId);
    } finally {
      setIsStreaming(false);
    }
  }

  async function ensureActiveSession(): Promise<ChatSession> {
    const currentSession = sessions.find(
      (session) => session.id === activeSessionId,
    );
    if (currentSession) {
      return currentSession;
    }

    const session = await createChatSession(workspaceId);
    setSessions((current) => [session, ...current]);
    setActiveSessionId(session.id);
    return session;
  }

  function applyFinalResponse(
    assistantMessageId: string,
    response: QueryResponse,
    attachedDocumentIds: string[],
  ) {
    setActiveSessionId(response.chat_session_id);
    setSessions((current) =>
      current.map((session) =>
        session.id === response.chat_session_id
          ? {
              ...session,
              title: response.chat_session_title,
              message_count: Math.max(session.message_count, messages.length + 2),
            }
          : session,
      ),
    );
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
              attachedDocumentIds,
              isFinal: true,
            }
          : message,
      ),
    );
  }

  function removeEmptyAssistantMessage(assistantMessageId: string) {
    setMessages((current) =>
      current.filter(
        (message) =>
          message.id !== assistantMessageId || message.content.trim().length > 0,
      ),
    );
  }

  function removeAttachment(documentId: string) {
    setSelectedAttachmentIds((current) =>
      current.filter((id) => id !== documentId),
    );
  }

  function documentsForMessage(documentIds: string[] | undefined) {
    return (documentIds ?? [])
      .map((id) => documentById.get(id))
      .filter((document): document is WorkspaceDocument => Boolean(document));
  }

  return (
    <DashboardShell
      activeItem="chat"
      title="Grounded chat"
      description="Ask questions against your indexed workspace sources and inspect cited evidence."
      workspaceId={workspaceId}
    >
      <PageHeader
        kicker="Chat"
        title="Ask questions, get cited answers"
        description="Use chat history for threads and attach documents from the input when you want focused retrieval."
      />

      <div className="grid gap-6 xl:grid-cols-[22rem_1fr]">
        <ChatSidebar
          sessions={sessions}
          activeSessionId={activeSessionId}
          isLoading={isSessionsLoading}
          errorMessage={sessionsError}
          isBusy={isStreaming}
          onNewChat={() => void handleNewChat()}
          onSelectSession={(sessionId) => void handleSelectSession(sessionId)}
          onRetry={() => void loadSessions()}
        />

        <section className="flex min-h-[calc(100dvh-12rem)] flex-col overflow-hidden rounded-3xl bg-card shadow-sm ring-1 ring-border/70">
          <div className="flex flex-col gap-3 border-b border-border px-5 py-4 sm:flex-row sm:items-start sm:justify-between">
            <div>
              <p className="text-sm font-medium text-muted-foreground">
                Active chat
              </p>
              <h2 className="mt-1 text-xl font-semibold tracking-tight text-card-foreground">
                {activeSession?.title ?? "New chat"}
              </h2>
              <p className="mt-1 text-sm text-muted-foreground">
                {attachedDocuments.length === 0
                  ? "No documents attached. The next question will search the whole workspace."
                  : `${attachedDocuments.length} ${
                      attachedDocuments.length === 1 ? "document" : "documents"
                    } attached for focused retrieval.`}
              </p>
            </div>
            {messages.length > 0 && (
              <Button
                variant="secondary"
                disabled={isStreaming}
                onClick={() => void handleNewChat()}
              >
                New chat
              </Button>
            )}
          </div>

          <div className="flex-1 space-y-5 overflow-y-auto bg-muted/30 px-4 py-5 sm:px-6">
            {isMessagesLoading ? (
              <LoadingState title="Loading messages" rows={4} />
            ) : messages.length === 0 && !isStreaming ? (
              <EmptyState
                title={
                  activeSessionId ? "Ask your first question" : "Start a chat"
                }
                description={
                  documents.length === 0
                    ? "Import documents before asking grounded questions."
                    : "Ask across the whole workspace, or attach specific documents from the input."
                }
                action={
                  documents.length === 0 ? (
                    <Button href={`/documents/${workspaceId}`}>
                      Import documents
                    </Button>
                  ) : undefined
                }
              />
            ) : (
              messages.map((message) => (
                <ChatMessage
                  key={message.id}
                  messageId={message.id}
                  role={message.role}
                  content={message.content}
                  citations={message.citations}
                  sources={message.sources}
                  confidence={message.confidence}
                  reviewFlags={message.reviewFlags}
                  isFinal={message.isFinal}
                  attachedDocuments={documentsForMessage(message.attachedDocumentIds)}
                  sourceById={sourceById}
                  onOpenSource={setSelectedSource}
                />
              ))
            )}

            <ChatThinkingState isThinking={isStreaming} />
          </div>

          {errorMessage && (
            <div className="border-t border-border px-5 py-3">
              <ErrorState
                message={errorMessage}
                action={
                  lastQuestion ? (
                    <Button
                      variant="secondary"
                      disabled={isStreaming}
                      onClick={() =>
                        void sendQuestion(lastQuestion.text, lastQuestion.documentIds)
                      }
                    >
                      Retry last question
                    </Button>
                  ) : undefined
                }
              />
            </div>
          )}

          <form
            onSubmit={(event) => void handleSubmit(event)}
            className="border-t border-border bg-card p-4"
          >
            <div className="rounded-2xl border border-input bg-background p-3 shadow-sm focus-within:ring-2 focus-within:ring-ring">
              {attachedDocuments.length > 0 && (
                <div className="mb-3">
                  <AttachedDocumentChips
                    documents={attachedDocuments}
                    onRemove={removeAttachment}
                  />
                </div>
              )}

              <div className="flex items-end gap-2">
                <button
                  type="button"
                  disabled={isStreaming}
                  onClick={() => setIsAttachModalOpen(true)}
                  className="grid h-10 w-10 shrink-0 place-items-center rounded-xl text-muted-foreground transition hover:bg-accent hover:text-accent-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:opacity-50"
                  aria-label="Attach documents"
                  title="Attach documents"
                >
                  <AttachIcon />
                </button>

                <textarea
                  id="chat-input"
                  value={input}
                  onChange={(event) => setInput(event.target.value)}
                  onKeyDown={(event) => {
                    if (event.key === "Enter" && !event.shiftKey) {
                      event.preventDefault();
                      void sendQuestion(input.trim());
                    }
                  }}
                  placeholder="Ask a question about your workspace..."
                  disabled={isStreaming}
                  maxLength={MAX_QUESTION_LENGTH}
                  rows={1}
                  className="max-h-40 min-h-10 flex-1 resize-none bg-transparent px-1 py-2 text-sm outline-none disabled:opacity-50"
                  aria-label="Chat input"
                />

                <Button
                  type="submit"
                  disabled={
                    isStreaming || !input.trim() || indexedDocuments.length === 0
                  }
                  className="shrink-0 px-5"
                >
                  {isStreaming ? "Sending..." : "Ask"}
                </Button>
              </div>
            </div>
            <div className="mt-2 flex flex-wrap items-center justify-between gap-2 text-xs text-muted-foreground">
              <span>
                {indexedDocuments.length.toLocaleString()} indexed{" "}
                {indexedDocuments.length === 1 ? "source" : "sources"} available
              </span>
              <span>
                {input.length.toLocaleString()} /{" "}
                {MAX_QUESTION_LENGTH.toLocaleString()} characters
              </span>
            </div>
          </form>
        </section>
      </div>

      <DocumentAttachModal
        key={isAttachModalOpen ? selectedAttachmentIds.join(",") : "closed"}
        isOpen={isAttachModalOpen}
        documents={documents}
        selectedIds={selectedAttachmentIds}
        isLoading={isDocumentsLoading}
        onClose={() => setIsAttachModalOpen(false)}
        onAttach={setSelectedAttachmentIds}
      />

      <SourceDrawer
        source={selectedSource}
        onClose={() => setSelectedSource(null)}
      />
    </DashboardShell>
  );
}

function historyMessageToChatMessage(
  message: ChatHistoryMessage,
): ChatMessageData {
  return {
    id: message.id,
    role: message.role === "assistant" ? "assistant" : "user",
    content: message.content,
    citations: message.citations,
    sources: message.source_list,
    attachedDocumentIds: message.attached_document_ids,
    isFinal: message.role === "assistant",
  };
}

function lastAttachedDocumentIds(messages: ChatHistoryMessage[]): string[] {
  for (let index = messages.length - 1; index >= 0; index -= 1) {
    const message = messages[index];
    if (message.attached_document_ids.length > 0) {
      return message.attached_document_ids;
    }
  }
  return [];
}

function AttachIcon() {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinecap="round"
      strokeLinejoin="round"
      className="h-5 w-5"
      aria-hidden="true"
    >
      <path d="m21.4 11.5-8.9 8.9a6 6 0 0 1-8.5-8.5l9.6-9.6a4 4 0 1 1 5.7 5.7l-9.7 9.7a2 2 0 1 1-2.8-2.8l8.9-8.9" />
    </svg>
  );
}
