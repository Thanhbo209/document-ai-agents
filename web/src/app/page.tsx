import Link from "next/link";

export default function Home() {
  return (
    <main className="min-h-screen bg-slate-950 text-white">
      <section className="mx-auto flex min-h-screen max-w-5xl flex-col items-start justify-center px-6">
        <p className="mb-4 rounded-full border border-slate-700 px-4 py-2 text-sm text-slate-300">
          Document AI Agent Platform
        </p>

        <h1 className="max-w-3xl text-5xl font-bold tracking-tight md:text-6xl">
          Upload documents, ask grounded questions, and review AI outputs
          safely.
        </h1>

        <p className="mt-6 max-w-2xl text-lg leading-8 text-slate-300">
          RAG Platform helps teams normalize documents, retrieve evidence,
          generate cited answers, extract structured data, compare files, and
          produce reviewable reports.
        </p>

        <div className="mt-8 flex gap-4">
          <Link
            href="/login"
            className="rounded-lg bg-white px-5 py-3 font-medium text-slate-950"
          >
            Log in
          </Link>

          <Link
            href="/register"
            className="rounded-lg border border-slate-700 px-5 py-3 font-medium text-slate-200"
          >
            Create account
          </Link>
        </div>
      </section>
    </main>
  );
}
