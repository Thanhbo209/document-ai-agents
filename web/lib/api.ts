const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000/api/v1";

export type DocumentFile = {
  id: string;
  filename: string;
  content_type: string;
  size_bytes: number;
  storage_key: string;
  checksum_sha256: string | null;
};

export type LatestJob = {
  id: string;
  status: string;
  error_message: string | null;
  created_at: string;
  updated_at: string;
};

export type WorkspaceDocument = {
  id: string;
  workspace_id: string;
  title: string;
  source_type: string;
  status: string;
  created_at: string;
  updated_at: string;
  files: DocumentFile[];
  latest_job: LatestJob | null;
  chunk_count: number;
};

export type DocumentListResponse = {
  workspace_id: string;
  total: number;
  documents: WorkspaceDocument[];
};

export type UploadDocumentResponse = {
  document_id: string;
  file_id: string;
  job_id: string;
  status: string;
  chunks_created: number;
};

type ListDocumentsParams = {
  query?: string;
  status?: string;
};

export async function listDocuments(
  workspaceId: string,
  params: ListDocumentsParams = {},
): Promise<DocumentListResponse> {
  const searchParams = new URLSearchParams();

  if (params.query) {
    searchParams.set("query", params.query);
  }

  if (params.status) {
    searchParams.set("status", params.status);
  }

  const queryString = searchParams.toString();
  const path = `/workspaces/${workspaceId}/documents${queryString ? `${queryString}` : ""}`;

  return apiRequest<DocumentListResponse>(path);
}

export async function uploadDocument(
  workspaceId: string,
  file: File,
): Promise<UploadDocumentResponse> {
  const formData = new FormData();
  formData.append("file", file);

  return apiRequest<UploadDocumentResponse>(
    `/workspaces/${workspaceId}/documents/upload`,
    {
      method: "POST",
      body: formData,
    },
  );
}

async function apiRequest<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    cache: "no-store",
  });

  if (!response.ok) {
    const errorBody = await safeReadJson(response);
    throw new Error(formatApiError(response.status, errorBody));
  }

  return response.json() as Promise<T>;
}

async function safeReadJson(response: Response): Promise<unknown> {
  try {
    return await response.json();
  } catch {
    return null;
  }
}

function formatApiError(status: number, body: unknown): string {
  if (body && typeof body === "object" && "detail" in body) {
    const detail = (body as { detail: unknown }).detail;

    if (typeof detail === "string") {
      return detail;
    }

    return JSON.stringify(detail);
  }

  return `Request failed with status ${status}.`;
}
