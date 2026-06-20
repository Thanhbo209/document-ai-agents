import Link from "next/link";

export default function Home() {
  const workspaceId = process.env.NEXT_PUBLIC_DEV_WORKSPACE_ID;

  return (
    <main className="min-h-screen bg-slate-950 text-white">
      <section className="mx-auto flex min-h-screen max-w-5xl flex-col items-start justify-center px-6">
        <p className="mb-4 rounded-full border border-slate-700 px-4 py-2 text-sm text-slate-300">
          Document AI Agent Platform
        </p>

        <h1 className="max-w-3xl text-5xl font-bold tracking-tight md:text-6xl">
          Upload documents, track ingestion, and build grounded AI workflows.
        </h1>

        <p className="mt-6 max-w-2xl text-lg leading-8 text-slate-300">
          RAG Platform helps teams normalize documents, retrieve evidence,
          generate cited answers, extract structured data, compare files, and
          produce reviewable reports.
        </p>

        <div className="mt-8 flex gap-4">
          {workspaceId ? (
            <Link
              href={`/workspaces/${workspaceId}`}
              className="rounded-lg bg-white px-5 py-3 font-medium text-slate-950"
            >
              Open workspace
            </Link>
          ) : (
            <span className="rounded-lg bg-slate-800 px-5 py-3 text-slate-300">
              Set NEXT_PUBLIC_DEV_WORKSPACE_ID
            </span>
          )}

          <a
            href="http://127.0.0.1:8000/docs"
            className="rounded-lg border border-slate-700 px-5 py-3 font-medium text-slate-200"
          >
            API docs
          </a>
        </div>
      </section>
    </main>
  );
}
