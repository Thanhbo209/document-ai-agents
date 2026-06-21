# Observability

The backend includes lightweight observability without external paid tools.

## Structured Logs

Set:

```text
RAG_PLATFORM_LOG_FORMAT=json
RAG_PLATFORM_LOG_LEVEL=INFO
```

JSON logs include timestamp, level, logger, message, service, environment, and
request ID when available. Request completion logs also include method, path,
status code, and duration in milliseconds.

## Request IDs

Every API response includes `X-Request-ID`.

- If the request provides `X-Request-ID`, the API preserves it.
- If missing, the API generates a UUID.
- Logs emitted during the request include the active request ID.

Use this ID to correlate frontend errors, API logs, and failed job records.

## Metrics

`GET /metrics` returns Prometheus-style counters:

- `rag_platform_requests_total`
- `rag_platform_requests_failed_total`
- `rag_platform_uploads_total`
- `rag_platform_queries_total`

Metrics are process-local and reset when the API process restarts. They are
useful for smoke checks and simple dashboards, not long-term analytics.

## Health And Readiness

- `GET /health` verifies the API process is running.
- `GET /ready` verifies the API can execute `SELECT 1` against the database.

Use readiness for deployment checks and health for basic process checks.

## Investigating Failed Ingestion Jobs

1. Find the request ID from the failed API response or frontend error.
2. Search API logs for the same `request_id`.
3. Check the document list for documents with `failed` status.
4. Inspect the latest ingestion job error message for the document.
5. Confirm the uploaded file exists in upload storage.
6. Retry with a known-good text file to separate extraction issues from storage
   or database issues.

## Future Work

- Persistent vector store.
- Durable metrics backend.
- Distributed tracing.
- Background worker metrics.
- Workspace deletion and retention enforcement.
