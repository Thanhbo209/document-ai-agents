import { QuerySource } from "../../lib/chat-api";

type SourceDrawerProps = {
  source: QuerySource | null;
  onClose: () => void;
};

export function SourceDrawer({ source, onClose }: SourceDrawerProps) {
  if (!source) {
    return null;
  }

  return (
    <aside className="fixed inset-y-0 right-0 z-50 w-full max-w-xl border-l border-slate-200 bg-white shadow-2xl">
      <div className="flex items-start justify-between border-b border-slate-200 px-6 py-4">
        <div>
          <p className="text-sm font-medium text-slate-500">
            Source {source.source_id}
          </p>
          <h2 className="mt-1 text-lg font-semibold text-slate-950">
            Citation context
          </h2>
        </div>

        <button
          type="button"
          onClick={onClose}
          className="rounded-lg border border-slate-200 px-3 py-1.5 text-sm text-slate-600 hover:bg-slate-50"
        >
          Close
        </button>
      </div>

      <div className="space-y-5 overflow-y-auto px-6 py-5">
        <div className="rounded-xl bg-slate-50 p-4 text-sm">
          <dl className="grid gap-3">
            <div>
              <dt className="font-medium text-slate-500">Document ID</dt>
              <dd className="mt-1 font-mono text-xs text-slate-800">
                {source.document_id}
              </dd>
            </div>

            <div>
              <dt className="font-medium text-slate-500">Chunk ID</dt>
              <dd className="mt-1 font-mono text-xs text-slate-800">
                {source.chunk_id}
              </dd>
            </div>

            <div className="grid grid-cols-3 gap-3">
              <div>
                <dt className="font-medium text-slate-500">Page</dt>
                <dd className="mt-1 text-slate-800">
                  {source.source_page ?? "N/A"}
                </dd>
              </div>

              <div>
                <dt className="font-medium text-slate-500">Start</dt>
                <dd className="mt-1 text-slate-800">
                  {source.source_start_offset ?? "N/A"}
                </dd>
              </div>

              <div>
                <dt className="font-medium text-slate-500">End</dt>
                <dd className="mt-1 text-slate-800">
                  {source.source_end_offset ?? "N/A"}
                </dd>
              </div>
            </div>

            <div>
              <dt className="font-medium text-slate-500">Score</dt>
              <dd className="mt-1 text-slate-800">{source.score.toFixed(3)}</dd>
            </div>
          </dl>
        </div>

        <div>
          <h3 className="text-sm font-semibold text-slate-900">Source span</h3>
          <pre className="mt-3 whitespace-pre-wrap rounded-xl bg-slate-950 p-4 text-sm leading-6 text-slate-100">
            {source.text}
          </pre>
        </div>
      </div>
    </aside>
  );
}
