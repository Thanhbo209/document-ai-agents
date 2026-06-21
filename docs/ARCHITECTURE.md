# Architecture

RAG Platform is organized around workspace-scoped document operations. The
backend owns tenancy, ingestion, retrieval, billing, audit, admin, and
compliance logic. The frontend presents user and admin dashboards over the API.

## High-Level Diagram

```txt
Browser
  |
  v
Next.js dashboard
  |
  v
FastAPI
  |
  +-- Auth and workspace permission dependencies
  +-- Upload, document, query, review, usage, billing, compliance routes
  +-- Admin/support metadata routes
  +-- Observability middleware
  |
  +-- SQLAlchemy repositories -> SQLite or PostgreSQL
  +-- Local upload storage
  +-- Hash embedder -> in-memory vector store
  +-- Retrieval and grounded answer generation
```

## Ingestion Pipeline

```txt
Upload file
  -> validate workspace permission and lifecycle status
  -> validate file name, file type, size, and quota
  -> create document, document file, and ingestion job
  -> store bytes in local upload storage
  -> load/normalize TXT, Markdown, or PDF
  -> chunk normalized text
  -> persist chunks and mark job succeeded
  -> record usage metrics
```

Expected ingestion errors, such as unsupported input or extraction failure, are
returned as user/application errors rather than generic 500s.

## Retrieval And Query Pipeline

```txt
Query request
  -> validate workspace permission and lifecycle status
  -> enforce daily query quota
  -> resolve selected document IDs inside workspace
  -> index workspace documents into runtime vector store
  -> embed query
  -> retrieve and rerank chunks
  -> generate extractive grounded answer
  -> validate citations
  -> persist conversation and citations
  -> record usage metrics
```

The current vector store is in-memory. It is suitable for tests and demos but
not production-safe because vectors are not durable across process restarts and
do not scale across multiple API instances.

## Citation Pipeline

Retrieved chunks become numbered answer sources. The local answer generator must
cite claims with source IDs such as `[S1]`. Citation validation rejects unknown
source references and answers without evidence. Persisted citations link
assistant messages back to chunk IDs for source inspection.

## Review Workflow

Review items capture AI-generated or extracted fields that need human approval.
Users with review permissions can create, approve, or reject review items. These
changes create audit events so decisions are traceable.

## Usage And Billing Flow

Usage events are recorded for uploads, document counts, chunks, query counts,
retrieval results, and token estimates. Each workspace has an internal
subscription record. The quota service resolves:

```txt
workspace -> subscription -> plan definition -> limit policy
```

Free and Pro plans are internal only. Stripe is intentionally not implemented in
this phase.

## Admin And Support Flow

Platform admins are separate from workspace owners. Admin routes require the
platform admin flag and expose operational metadata:

- Workspace metadata and owner email.
- Ingestion jobs and errors.
- Document metadata, file count, and chunk count.
- Usage/billing metadata.
- Audit events and audit export.

Admin/support views must not expose raw document text, chunk text, uploaded file
contents, or conversation message content by default.

## Compliance Flow

Workspace owners with manage permission can export workspace-owned data and
request deletion. Deletion is a lifecycle transition:

```txt
active -> pending_deletion -> deleted
```

Pending and deleted workspaces are blocked from normal upload/query/document
routes. Rows and uploaded files are not physically deleted yet. Permanent
deletion, backup coordination, retention scheduling, legal hold, and
break-glass access are future work.

## Observability

The API includes:

- `/health`
- `/ready`
- `/metrics`
- Request IDs via `X-Request-ID`
- Structured JSON logging support
- Basic security headers

## Known Limitations

- In-memory vector store is not production-safe.
- Local deterministic AI adapters are used by default.
- No external LLM provider is required for tests or demos.
- No Stripe, SSO/SAML, SCIM, or external observability provider.
- No permanent deletion worker or legal hold.
- Local upload storage should be replaced with production object storage before
  real deployment.
- This is a product-level compliance foundation, not certification.
