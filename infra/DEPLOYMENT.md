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
