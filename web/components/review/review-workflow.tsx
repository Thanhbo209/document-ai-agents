"use client";

import { useCallback, useEffect, useState } from "react";
import {
  approveReviewItem,
  listReviewItems,
  rejectReviewItem,
  reviewExportUrl,
  ReviewItem,
} from "../../lib/review-api";
import { DashboardShell } from "../layout/dashboard-shell";
import { Button } from "../ui/button";
import { EmptyState } from "../ui/empty-state";
import { ErrorState } from "../ui/error-state";
import { LoadingState } from "../ui/loading-state";
import { PageHeader } from "../ui/page-header";
import { StatCard } from "../ui/stat-card";
import { StatusBadge } from "../ui/status-badge";

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

  const pending = items.filter((item) => item.status === "pending").length;
  const approved = items.filter((item) => item.status === "approved").length;
  const rejected = items.filter((item) => item.status === "rejected").length;

  return (
    <DashboardShell
      activeItem="review"
      title="Review workflows"
      description="Approve or reject extracted values, generated report sections, and agent actions."
      workspaceId={workspaceId}
    >
      <PageHeader
        kicker="Human review"
        title="Decision queue with an audit trail"
        description="Work through pending items, add reviewer notes, and export decisions for operational follow-up."
        meta={
          <p className="font-mono text-xs text-muted-foreground">{workspaceId}</p>
        }
        actions={
          <>
            <a
              href={reviewExportUrl(workspaceId, "json", status || undefined)}
              className="inline-flex items-center justify-center rounded-xl border border-border bg-card px-4 py-2.5 text-sm font-medium text-card-foreground shadow-sm transition hover:-translate-y-0.5 hover:bg-accent"
            >
              Export JSON
            </a>
            <a
              href={reviewExportUrl(workspaceId, "csv", status || undefined)}
              className="inline-flex items-center justify-center rounded-xl border border-border bg-card px-4 py-2.5 text-sm font-medium text-card-foreground shadow-sm transition hover:-translate-y-0.5 hover:bg-accent"
            >
              Export CSV
            </a>
          </>
        }
      />

      <section className="mb-6 grid grid-flow-dense gap-4 sm:grid-cols-3">
        <StatCard
          label="Pending"
          value={pending}
          detail="Awaiting reviewer action"
          tone="warning"
        />
        <StatCard
          label="Approved"
          value={approved}
          detail="Accepted decisions"
          tone="good"
        />
        <StatCard
          label="Rejected"
          value={rejected}
          detail="Returned for correction"
          tone={rejected > 0 ? "danger" : "neutral"}
        />
      </section>

      <section className="mb-6 rounded-3xl bg-card p-5 shadow-sm ring-1 ring-border/70">
        <div className="grid gap-3 md:grid-cols-[220px_auto_1fr]">
          <select
            value={status}
            onChange={(event) => setStatus(event.target.value)}
            className="rounded-xl border border-input bg-background px-4 py-2.5 text-sm outline-none transition focus:ring-2 focus:ring-ring"
          >
            <option value="">All statuses</option>
            <option value="pending">Pending</option>
            <option value="approved">Approved</option>
            <option value="rejected">Rejected</option>
          </select>

          <Button onClick={() => void refresh()}>Refresh queue</Button>
        </div>

        {errorMessage && (
          <div className="mt-4">
            <ErrorState message={errorMessage} />
          </div>
        )}
      </section>

      {isLoading ? (
        <LoadingState title="Loading review items" />
      ) : items.length === 0 ? (
        <EmptyState
          title="No review items found"
          description="The current filters do not have pending or completed decisions."
        />
      ) : (
        <section className="space-y-4">
          {items.map((item) => (
            <article
              key={item.id}
              className="rounded-3xl bg-card p-5 shadow-sm ring-1 ring-border/70"
            >
              <div className="flex flex-wrap items-start justify-between gap-4">
                <div>
                  <p className="text-sm font-medium text-muted-foreground">
                    {item.target_type}
                  </p>
                  <h2 className="mt-1 text-xl font-semibold tracking-tight text-card-foreground">
                    {item.field_name ?? item.target_id}
                  </h2>
                  <p className="mt-2 font-mono text-xs text-muted-foreground">
                    {item.id}
                  </p>
                </div>

                <StatusBadge status={item.status} />
              </div>

              <div className="mt-5 grid gap-4 lg:grid-cols-3">
                <JsonCard title="Original value" value={item.original_value} />
                <JsonCard title="Reviewed value" value={item.reviewed_value} />
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
                    className="rounded-xl border border-input bg-background px-4 py-2.5 text-sm outline-none transition focus:ring-2 focus:ring-ring"
                  />

                  <Button onClick={() => void approve(item)}>Approve</Button>
                  <Button variant="danger" onClick={() => void reject(item)}>
                    Reject
                  </Button>
                </div>
              ) : (
                <div className="mt-5 rounded-2xl bg-muted px-4 py-3 text-sm text-muted-foreground">
                  Reviewed by {item.reviewer_user_id ?? "unknown"} at{" "}
                  {item.reviewed_at
                    ? new Date(item.reviewed_at).toLocaleString()
                    : "unknown time"}
                  {item.comments ? ` - ${item.comments}` : ""}
                </div>
              )}
            </article>
          ))}
        </section>
      )}
    </DashboardShell>
  );
}

function JsonCard({ title, value }: { title: string; value: unknown }) {
  return (
    <div className="rounded-2xl bg-muted/70 p-4">
      <h3 className="text-sm font-semibold text-card-foreground">{title}</h3>
      <pre className="mt-3 max-h-52 overflow-auto whitespace-pre-wrap text-xs leading-5 text-muted-foreground">
        {JSON.stringify(value, null, 2)}
      </pre>
    </div>
  );
}
