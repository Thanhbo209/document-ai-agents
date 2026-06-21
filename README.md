# RAG Platform

RAG Platform is a multi-tenant document AI platform for uploading operational
documents, asking grounded questions with citations, reviewing AI outputs, and
managing tenant controls.

It is not just a chatbot over PDFs. The project is a document operations layer:
ingestion, chunking, retrieval, cited answers, structured extraction, review
workflows, usage metering, billing-plan enforcement, admin/support tooling, and
basic compliance controls.

## What It Solves

Teams often need to turn messy internal documents into reliable answers and
reviewable workflows. RAG Platform demonstrates how to build that system with
workspace tenancy, evidence-backed responses, operational dashboards, audit
events, and release-friendly deployment posture.

## Core Features

- JWT authentication with workspace membership and role-based permissions.
- Workspace-scoped document upload, parsing, chunking, and ingestion jobs.
- Local retrieval over indexed chunks with grounded answers and citations.
- Source drawer for inspecting answer evidence.
- Structured extraction, document comparison, and report generation modules.
- Review workflow for human approval/rejection of AI-generated items.
- Usage metering for uploads, documents, chunks, queries, retrieval, and tokens.
- Internal free/pro billing plans with quota enforcement.
- Platform admin console for metadata, failed jobs, billing metadata, and audit
  events.
- Compliance controls for workspace export, soft deletion, lifecycle status, and
  security headers.
- Observability baseline with health, readiness, metrics, request IDs, and JSON
  logging support.
- Docker production baseline for API, web, and PostgreSQL.

## Architecture Overview

```txt
Next.js dashboard
  -> FastAPI API
      -> Auth and workspace tenancy
      -> Upload and ingestion pipeline
      -> SQLAlchemy models and repositories
      -> Local file storage
      -> Hash embedder and in-memory vector store
      -> Retrieval, reranking, grounded answer generation
      -> Usage, billing, audit, admin, and compliance services
  -> PostgreSQL or SQLite
```

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for pipeline details and
tradeoffs.

## Backend Stack

- FastAPI
- SQLAlchemy
- Alembic
- Pydantic settings
- Pytest
- Ruff
- Local SQLite for development and tests
- PostgreSQL in production compose

## Frontend Stack

- Next.js App Router
- React
- TypeScript
- Tailwind CSS
- Responsive dashboard shell with fixed/collapsible sidebar
- Light/dark theme tokens

## AI And RAG Pipeline

The default local pipeline is deterministic and self-contained:

1. Upload document files.
2. Normalize text from TXT, Markdown, or PDF.
3. Chunk text with token overlap.
4. Embed chunks with a local hash embedder.
5. Store vectors in an in-memory vector store.
6. Retrieve and rerank chunks for a query.
7. Generate an extractive grounded answer.
8. Validate citations and persist conversation/citation records.

This keeps demos and tests offline. It is intentionally not wired to a paid
external LLM provider by default.

## Security And Tenancy

- Users authenticate with JWTs.
- Workspaces have owner/member roles and permission policies.
- Workspace-scoped routes enforce tenancy through FastAPI dependencies.
- Pending-deletion and deleted workspaces are blocked from normal app routes.
- Platform admin routes are separate from workspace owner routes.
- Admin/support views are metadata-first and do not expose raw document or
  chunk text by default.
- API responses include request IDs and baseline security headers.

## Admin And Compliance Controls

- Platform admins can inspect workspace metadata, failed ingestion jobs, usage
  and billing metadata, and audit events.
- Owners can export workspace-owned data as JSON.
- Owners can request workspace deletion, which soft-deletes the workspace first.
- Compliance actions create audit events.
- Permanent deletion is future work.

## Local Setup

Requirements:

- Python 3.14+
- Node.js compatible with Next.js 16
- npm

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"

cd web
npm install
cd ..
```

Copy environment defaults if needed:

```powershell
Copy-Item .env.example .env
```

## Environment Variables

The backend uses the `RAG_PLATFORM_` prefix. Important variables:

- `RAG_PLATFORM_DATABASE_URL`
- `RAG_PLATFORM_UPLOAD_DIR`
- `RAG_PLATFORM_JWT_SECRET_KEY`
- `RAG_PLATFORM_CORS_ALLOWED_ORIGINS`
- `RAG_PLATFORM_LOG_FORMAT`
- `RAG_PLATFORM_METRICS_ENABLED`

The frontend uses:

- `NEXT_PUBLIC_API_BASE_URL`

See [.env.example](.env.example) and [infra/DEPLOYMENT.md](infra/DEPLOYMENT.md).

## Migrations

```powershell
.\.venv\Scripts\alembic.exe upgrade head
```

Create a migration after model changes:

```powershell
.\.venv\Scripts\alembic.exe revision --autogenerate -m "describe change"
```

## Run The App Locally

Backend:

```powershell
.\.venv\Scripts\uvicorn.exe app.main:app --reload
```

Frontend:

```powershell
cd web
npm run dev
```

Open:

```txt
http://127.0.0.1:3000
```

## Quality Gates

Run everything:

```powershell
.\scripts\check_all.ps1
```

Backend only:

```powershell
.\.venv\Scripts\ruff.exe format .
.\.venv\Scripts\ruff.exe check .
.\.venv\Scripts\pytest.exe -q
.\.venv\Scripts\python.exe -m evals.run
```

Frontend only:

```powershell
cd web
npm run lint
npm run build
cd ..
```

## Docker Compose

Production-like local stack:

```powershell
docker compose -f docker-compose.prod.yml up --build
```

Smoke check:

```powershell
.\scripts\prod_smoke.ps1
```

## Demo Flow

1. Register or log in.
2. Open the default workspace.
3. Upload a TXT, Markdown, or PDF document.
4. Ask a grounded question in chat.
5. Open citations and inspect source evidence.
6. Create or review AI output.
7. View usage and billing plan limits.
8. Export workspace data from settings.
9. Log in as a platform admin and inspect workspaces, jobs, and audit events.

See [docs/DEMO_SCRIPT.md](docs/DEMO_SCRIPT.md) for a detailed walkthrough and
interview talking points.

## Known Limitations

- The vector store is in-memory and not production-safe.
- The default embedder and answer generator are local deterministic adapters,
  not external hosted AI providers.
- No Stripe or real payment processing yet.
- No permanent deletion worker yet.
- No SSO/SAML/SCIM yet.
- Upload storage is local volume storage by default, not production-grade object
  storage.
- This project is not SOC 2 certified and does not claim legal compliance.

## Future Work

- Durable vector database.
- Background ingestion/indexing worker.
- External LLM and embedding provider adapters.
- Object storage integration.
- Stripe-backed subscription lifecycle.
- Permanent deletion and retention scheduler.
- Legal hold and break-glass access workflow.
- SSO/SAML and SCIM.
- Stronger CSP and production security hardening.
