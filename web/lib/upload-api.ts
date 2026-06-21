import { apiRequest } from "./api";

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
  const path = `/workspaces/${workspaceId}/documents${queryString ? `?${queryString}` : ""}`;

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
