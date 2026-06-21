import { API_BASE_URL, apiRequest, formatApiError, safeReadJson } from "./api";
import { getAccessToken } from "./auth-api";

export type QueryCitation = {
  source_id: string;
  chunk_id: string;
  document_id: string;
  workspace_id: string;
  source_page: number | null;
  source_start_offset: number | null;
  source_end_offset: number | null;
  quote: string;
  metadata: Record<string, unknown>;
};

export type QuerySource = {
  source_id: string;
  chunk_id: string;
  document_id: string;
  workspace_id: string;
  text: string;
  source_page: number | null;
  source_start_offset: number | null;
  source_end_offset: number | null;
  score: number;
  metadata: Record<string, unknown>;
};

export type QueryResponse = {
  user_message_id: string;
  assistant_message_id: string;
  message: string;
  citations: QueryCitation[];
  source_list: QuerySource[];
  confidence: number;
  review_flags: string[];
  model_name: string;
  prompt_id: string;
};

export type StreamQueryInput = {
  query: string;
  document_ids?: string[];
  top_k?: number;
};

export type StreamQueryHandlers = {
  onStart?: (data: { assistant_message_id: string }) => void;
  onToken?: (text: string) => void;
  onFinal?: (response: QueryResponse) => void;
  onError?: (message: string) => void;
};

export async function queryWorkspace(
  workspaceId: string,
  input: StreamQueryInput,
): Promise<QueryResponse> {
  return apiRequest<QueryResponse>(`/workspaces/${workspaceId}/query`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(input),
  });
}

export async function streamWorkspaceQuery(
  workspaceId: string,
  input: StreamQueryInput,
  handlers: StreamQueryHandlers,
): Promise<void> {
  const token = getAccessToken();

  const headers = new Headers({
    "Content-Type": "application/json",
  });

  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }
  const response = await fetch(
    `${API_BASE_URL}/workspaces/${workspaceId}/query/stream`,
    {
      method: "POST",
      headers: headers,
      body: JSON.stringify(input),
    },
  );

  if (!response.ok) {
    const errorBody = await safeReadJson(response);
    throw new Error(formatApiError(response.status, errorBody));
  }

  if (!response.body) {
    throw new Error("Streaming response body is not available.");
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();

  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();

    if (done) {
      break;
    }

    buffer += decoder.decode(value, { stream: true });

    const events = buffer.split("\n\n");
    buffer = events.pop() ?? "";

    for (const rawEvent of events) {
      handleSseEvent(rawEvent, handlers);
    }
  }

  if (buffer.trim()) {
    handleSseEvent(buffer, handlers);
  }
}

function handleSseEvent(rawEvent: string, handlers: StreamQueryHandlers): void {
  const lines = rawEvent.split("\n");
  const eventLine = lines.find((line) => line.startsWith("event:"));
  const dataLine = lines.find((line) => line.startsWith("data:"));

  if (!eventLine || !dataLine) {
    return;
  }

  const event = eventLine.replace("event:", "").trim();
  const data = JSON.parse(dataLine.replace("data:", "").trim()) as unknown;

  if (event === "start") {
    handlers.onStart?.(data as { assistant_message_id: string });
  }

  if (event === "token") {
    const tokenData = data as { text: string };
    handlers.onToken?.(tokenData.text);
  }

  if (event === "final") {
    handlers.onFinal?.(data as QueryResponse);
  }

  if (event === "error") {
    const errorData = data as { message: string };
    handlers.onError?.(errorData.message);
  }
}
