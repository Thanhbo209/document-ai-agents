# Deployment

This project can run as a small production-like Docker Compose stack without
Kubernetes or Terraform.

## Services

- `postgres`: PostgreSQL database with a persistent Docker volume.
- `api`: FastAPI backend running Uvicorn. It runs `alembic upgrade head` before
  serving traffic.
- `web`: Next.js frontend built with `output: "standalone"`.

## Required Environment

Backend settings use the `RAG_PLATFORM_` prefix.

| Variable | Purpose |
| --- | --- |
| `RAG_PLATFORM_SERVICE_NAME` | Service name used in logs and health output. |
| `RAG_PLATFORM_ENVIRONMENT` | Deployment environment, for example `production`. |
| `RAG_PLATFORM_DEBUG` | Set to `false` in production. |
| `RAG_PLATFORM_DATABASE_URL` | SQLAlchemy database URL. |
| `RAG_PLATFORM_UPLOAD_DIR` | Persistent upload directory. |
| `RAG_PLATFORM_JWT_SECRET_KEY` | JWT signing secret. Replace all placeholders. |
| `RAG_PLATFORM_LOG_LEVEL` | Log level, usually `INFO`. |
| `RAG_PLATFORM_LOG_FORMAT` | Use `json` for production logs. |
| `RAG_PLATFORM_METRICS_ENABLED` | Enables `/metrics` when `true`. |
| `RAG_PLATFORM_MEDIA_ASYNC_ENABLED` | Processes media uploads with in-process background tasks. |
| `RAG_PLATFORM_MEDIA_MAX_SYNC_SIZE_BYTES` | Maximum media size considered safe for synchronous processing when async is disabled. |
| `RAG_PLATFORM_WHISPER_MODEL_NAME` | Local Whisper model name, for example `base`. |
| `RAG_PLATFORM_CONNECTOR_WEB_ALLOWED_DOMAINS` | Optional JSON list of domains allowed for web connector fetches. |
| `RAG_PLATFORM_CONNECTOR_WEB_BLOCKED_DOMAINS` | Optional JSON list of domains blocked for web connector fetches. |
| `RAG_PLATFORM_CONNECTOR_WEB_MAX_RESPONSE_BYTES` | Maximum response bytes fetched by the web connector. |
| `RAG_PLATFORM_CONNECTOR_WEB_TIMEOUT_SECONDS` | Timeout for web connector fetches. |
| `RAG_PLATFORM_REPO_INGESTION_MAX_FILES` | Maximum files read from a repository ZIP upload. |
| `RAG_PLATFORM_REPO_INGESTION_MAX_TOTAL_BYTES` | Maximum total bytes read from a repository ZIP upload. |
| `RAG_PLATFORM_REPO_INGESTION_MAX_FILE_BYTES` | Maximum bytes read from one repository file. |
| `RAG_PLATFORM_CORS_ALLOWED_ORIGINS` | JSON list of allowed frontend origins. |

Frontend builds use:

| Variable | Purpose |
| --- | --- |
| `NEXT_PUBLIC_API_BASE_URL` | Browser-visible API base URL, including `/api/v1`. |

## Local Production Stack

Review `docker-compose.prod.yml` and replace every `CHANGE_ME_*` value before
using it outside local testing.

```powershell
docker compose -f docker-compose.prod.yml up --build
```

Then check:

```powershell
./scripts/prod_smoke.ps1
```

## Endpoints

- `GET /health`: process health and service metadata.
- `GET /ready`: database readiness check using `SELECT 1`.
- `GET /metrics`: Prometheus-style text metrics when enabled.

## Media Processing

Media transcription uses local FFmpeg and local Whisper, not hosted paid APIs. If
media ingestion is enabled, the API host or image must include the `ffmpeg`
system binary and enough CPU/memory for the selected Whisper model. The current
implementation uses FastAPI background tasks for large media; production
deployments should eventually move transcription to a dedicated worker queue.

## Connector Processing

Web connector ingestion requires outbound HTTPS access from the API host. Keep
domain allowlists/blocklists strict for controlled deployments, and remember that
the connector intentionally blocks localhost and private/internal IP ranges.

YouTube transcript ingestion depends on transcript availability and the
`youtube-transcript-api` package. Repository ZIP ingestion is local-only and does
not clone arbitrary Git URLs; uploaded ZIPs are filtered for safe paths, file
types, and size limits.

## Deployment Order

1. Provision PostgreSQL and upload storage.
2. Set backend secrets and environment variables.
3. Build and deploy the API image.
4. Run `alembic upgrade head`.
5. Start the API and verify `/ready`.
6. Build and deploy the frontend with the public API URL.
7. Run the smoke script and review structured logs.

## Known Limitation

The app still uses an in-memory vector store. This is not production-safe:
vectors are process-local, are lost on restart, and are not shared across API
instances. Use a persistent vector database before relying on this deployment
for durable production retrieval.
