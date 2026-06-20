"use client";

import { useCallback, useEffect, useState } from "react";
import {
  approveReviewItem,
  listReviewItems,
  rejectReviewItem,
  reviewExportUrl,
  ReviewItem,
} from "../../lib/review-api";

type ReviewWorkflowProps = {
  workspaceId: string;
};

export function ReviewWorkflow({ workspaceId }: ReviewWorkflowProps) {
  const [items, setItems] = useState<ReviewItem[]>([]);
  const [status, setStatus] = useState("");
  const [commentsById, setCommentsById] = useState<Record<string, string>>({});
  const [isLoading, setIsLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    setIsLoading(true);
    setErrorMessage(null);

    try {
      const data = await listReviewItems(workspaceId, status || undefined);
      setItems(data);
    } catch (error) {
      setErrorMessage(
        error instanceof Error ? error.message : "Could not load review items.",
      );
    } finally {
      setIsLoading(false);
    }
  }, [workspaceId, status]);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    void refresh();
  }, [refresh]);

  async function approve(item: ReviewItem) {
    await approveReviewItem(workspaceId, item.id, {
      reviewer_user_id: "dev-reviewer",
      reviewed_value: item.original_value ?? undefined,
      comments: commentsById[item.id],
    });
    await refresh();
  }

  async function reject(item: ReviewItem) {
    await rejectReviewItem(workspaceId, item.id, {
      reviewer_user_id: "dev-reviewer",
      comments: commentsById[item.id],
    });
    await refresh();
  }

  return (
    <main className="min-h-screen bg-slate-50 px-6 py-8">
      <div className="mx-auto max-w-7xl">
        <header className="mb-8">
          <p className="text-sm font-medium text-slate-500">Workspace review</p>
          <h1 className="mt-2 text-3xl font-bold tracking-tight text-slate-950">
            Review workflows
          </h1>
          <p className="mt-2 max-w-2xl text-slate-600">
            Approve or reject extracted values, generated report sections, and
            agent actions. Every decision is recorded in the audit trail.
          </p>
          <p className="mt-3 font-mono text-xs text-slate-400">{workspaceId}</p>
        </header>

        <section className="mb-6 rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
          <div className="grid gap-4 md:grid-cols-[220px_auto_auto_auto_1fr]">
            <select
              value={status}
              onChange={(event) => setStatus(event.target.value)}
              className="rounded-lg border border-slate-300 px-4 py-2 text-sm"
            >
              <option value="">All statuses</option>
              <option value="pending">Pending</option>
              <option value="approved">Approved</option>
              <option value="rejected">Rejected</option>
            </select>

            <button
              type="button"
              onClick={() => void refresh()}
              className="rounded-lg bg-slate-950 px-4 py-2 text-sm font-medium text-white"
            >
              Refresh
            </button>

            <a
              href={reviewExportUrl(workspaceId, "json", status || undefined)}
              className="rounded-lg border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700"
            >
              Export JSON
            </a>

            <a
              href={reviewExportUrl(workspaceId, "csv", status || undefined)}
              className="rounded-lg border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700"
            >
              Export CSV
            </a>
          </div>

          {errorMessage && (
            <p className="mt-4 rounded-lg bg-red-50 px-4 py-3 text-sm text-red-700">
              {errorMessage}
            </p>
          )}
        </section>

        {isLoading ? (
          <div className="rounded-2xl border border-slate-200 bg-white p-10 text-center text-slate-500">
            Loading review items...
          </div>
        ) : (
          <section className="space-y-4">
            {items.map((item) => (
              <article
                key={item.id}
                className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm"
              >
                <div className="flex flex-wrap items-start justify-between gap-4">
                  <div>
                    <p className="text-xs font-medium uppercase tracking-wide text-slate-500">
                      {item.target_type}
                    </p>
                    <h2 className="mt-1 text-lg font-semibold text-slate-950">
                      {item.field_name ?? item.target_id}
                    </h2>
                    <p className="mt-1 font-mono text-xs text-slate-400">
                      {item.id}
                    </p>
                  </div>

                  <StatusBadge status={item.status} />
                </div>

                <div className="mt-5 grid gap-4 md:grid-cols-3">
                  <JsonCard
                    title="Original value"
                    value={item.original_value}
                  />
                  <JsonCard
                    title="Reviewed value"
                    value={item.reviewed_value}
                  />
                  <JsonCard title="Evidence" value={item.evidence} />
                </div>

                {item.status === "pending" ? (
                  <div className="mt-5 grid gap-3 md:grid-cols-[1fr_auto_auto]">
                    <input
                      value={commentsById[item.id] ?? ""}
                      onChange={(event) =>
                        setCommentsById((current) => ({
                          ...current,
                          [item.id]: event.target.value,
                        }))
                      }
                      placeholder="Reviewer comments..."
                      className="rounded-lg border border-slate-300 px-4 py-2 text-sm"
                    />

                    <button
                      type="button"
                      onClick={() => void approve(item)}
                      className="rounded-lg bg-emerald-600 px-4 py-2 text-sm font-medium text-white"
                    >
                      Approve
                    </button>

                    <button
                      type="button"
                      onClick={() => void reject(item)}
                      className="rounded-lg bg-red-600 px-4 py-2 text-sm font-medium text-white"
                    >
                      Reject
                    </button>
                  </div>
                ) : (
                  <div className="mt-5 rounded-lg bg-slate-50 px-4 py-3 text-sm text-slate-600">
                    Reviewed by {item.reviewer_user_id ?? "unknown"} at{" "}
                    {item.reviewed_at
                      ? new Date(item.reviewed_at).toLocaleString()
                      : "unknown time"}
                    {item.comments ? ` — ${item.comments}` : ""}
                  </div>
                )}
              </article>
            ))}

            {items.length === 0 && (
              <div className="rounded-2xl border border-dashed border-slate-300 bg-white p-10 text-center text-slate-500">
                No review items found.
              </div>
            )}
          </section>
        )}
      </div>
    </main>
  );
}

function JsonCard({ title, value }: { title: string; value: unknown }) {
  return (
    <div className="rounded-xl bg-slate-50 p-4">
      <h3 className="text-sm font-semibold text-slate-900">{title}</h3>
      <pre className="mt-3 max-h-52 overflow-auto whitespace-pre-wrap text-xs text-slate-700">
        {JSON.stringify(value, null, 2)}
      </pre>
    </div>
  );
}

function StatusBadge({ status }: { status: string }) {
  const className =
    status === "approved"
      ? "bg-emerald-50 text-emerald-700 ring-emerald-200"
      : status === "rejected"
        ? "bg-red-50 text-red-700 ring-red-200"
        : "bg-amber-50 text-amber-700 ring-amber-200";

  return (
    <span
      className={`rounded-full px-3 py-1 text-xs font-medium ring-1 ${className}`}
    >
      {status}
    </span>
  );
}
