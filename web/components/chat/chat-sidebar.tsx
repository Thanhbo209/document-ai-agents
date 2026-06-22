"use client";

import { ChatSession } from "../../lib/chat-api";
import { formatRelativeTime } from "../../lib/format";
import { Button } from "../ui/button";
import { EmptyState } from "../ui/empty-state";
import { ErrorState } from "../ui/error-state";
import { LoadingState } from "../ui/loading-state";

type ChatSidebarProps = {
  sessions: ChatSession[];
  activeSessionId: string | null;
  isLoading: boolean;
  errorMessage: string | null;
  isBusy?: boolean;
  onNewChat: () => void;
  onSelectSession: (sessionId: string) => void;
  onRetry: () => void;
};

export function ChatSidebar({
  sessions,
  activeSessionId,
  isLoading,
  errorMessage,
  isBusy = false,
  onNewChat,
  onSelectSession,
  onRetry,
}: ChatSidebarProps) {
  return (
    <aside className="rounded-3xl bg-card p-5 shadow-sm ring-1 ring-border/70">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-sm font-medium text-muted-foreground">History</p>
          <h2 className="mt-1 text-xl font-semibold tracking-tight text-card-foreground">
            Chat sessions
          </h2>
        </div>
        <Button disabled={isBusy} onClick={onNewChat}>
          New chat
        </Button>
      </div>

      <p className="mt-3 text-sm leading-6 text-muted-foreground">
        Pick up a previous thread, or start fresh for a new line of inquiry.
      </p>

      <div className="mt-5 space-y-2">
        {isLoading ? (
          <LoadingState title="Loading chats" rows={4} />
        ) : errorMessage ? (
          <ErrorState
            message={errorMessage}
            action={
              <Button variant="secondary" onClick={onRetry}>
                Try again
              </Button>
            }
          />
        ) : sessions.length === 0 ? (
          <EmptyState
            title="No chats yet"
            description="Start a new chat, ask a question, and it will appear here."
          />
        ) : (
          sessions.map((session) => (
            <button
              key={session.id}
              type="button"
              disabled={isBusy}
              onClick={() => onSelectSession(session.id)}
              className={[
                "w-full rounded-2xl border p-3 text-left transition duration-200",
                "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:opacity-60",
                session.id === activeSessionId
                  ? "border-primary/50 bg-primary/10 shadow-sm"
                  : "border-border bg-background/70 hover:-translate-y-0.5 hover:bg-accent",
              ].join(" ")}
              aria-current={session.id === activeSessionId ? "page" : undefined}
            >
              <span className="block truncate text-sm font-semibold text-card-foreground">
                {session.title || "New chat"}
              </span>
              <span className="mt-1 flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
                <span>{formatRelativeTime(session.updated_at)}</span>
                <span>
                  {session.message_count.toLocaleString()}{" "}
                  {session.message_count === 1 ? "message" : "messages"}
                </span>
              </span>
            </button>
          ))
        )}
      </div>
    </aside>
  );
}
