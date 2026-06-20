import { WorkspaceDocument } from "../../lib/upload-api";

type DocumentTableProps = {
  documents: WorkspaceDocument[];
};

export function DocumentTable({ documents }: DocumentTableProps) {
  return (
    <section className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
      <div className="border-b border-slate-200 px-6 py-4">
        <h2 className="text-lg font-semibold text-slate-900">Documents</h2>
        <p className="text-sm text-slate-500">
          Search metadata, inspect status, and review failed ingestion causes.
        </p>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full min-w-225 text-left text-sm">
          <thead className="bg-slate-50 text-xs uppercase tracking-wide text-slate-500">
            <tr>
              <th className="px-6 py-3">Title</th>
              <th className="px-6 py-3">Type</th>
              <th className="px-6 py-3">Status</th>
              <th className="px-6 py-3">Chunks</th>
              <th className="px-6 py-3">File</th>
              <th className="px-6 py-3">Latest job</th>
              <th className="px-6 py-3">Updated</th>
            </tr>
          </thead>

          <tbody className="divide-y divide-slate-100">
            {documents.map((document) => (
              <tr key={document.id} className="align-top">
                <td className="px-6 py-4">
                  <p className="font-medium text-slate-900">{document.title}</p>
                  <p className="mt-1 font-mono text-xs text-slate-400">
                    {document.id}
                  </p>
                </td>

                <td className="px-6 py-4 text-slate-600">
                  {document.source_type}
                </td>

                <td className="px-6 py-4">
                  <StatusBadge status={document.status} />
                </td>

                <td className="px-6 py-4 text-slate-600">
                  {document.chunk_count}
                </td>

                <td className="px-6 py-4 text-slate-600">
                  {document.files[0]?.filename ?? "No file"}
                </td>

                <td className="px-6 py-4">
                  {document.latest_job ? (
                    <div>
                      <p className="text-slate-700">
                        {document.latest_job.status}
                      </p>
                      {document.latest_job.error_message && (
                        <p className="mt-1 max-w-xs text-xs text-red-600">
                          {document.latest_job.error_message}
                        </p>
                      )}
                    </div>
                  ) : (
                    <span className="text-slate-400">No job</span>
                  )}
                </td>

                <td className="px-6 py-4 text-slate-500">
                  {new Date(document.updated_at).toLocaleString()}
                </td>
              </tr>
            ))}

            {documents.length === 0 && (
              <tr>
                <td
                  colSpan={7}
                  className="px-6 py-12 text-center text-slate-500"
                >
                  No documents found.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </section>
  );
}

function StatusBadge({ status }: { status: string }) {
  const className =
    status === "indexed"
      ? "bg-emerald-50 text-emerald-700 ring-emerald-200"
      : status === "failed"
        ? "bg-red-50 text-red-700 ring-red-200"
        : status === "processing"
          ? "bg-amber-50 text-amber-700 ring-amber-200"
          : "bg-slate-100 text-slate-700 ring-slate-200";

  return (
    <span
      className={`inline-flex rounded-full px-2.5 py-1 text-xs font-medium ring-1 ${className}`}
    >
      {status}
    </span>
  );
}
