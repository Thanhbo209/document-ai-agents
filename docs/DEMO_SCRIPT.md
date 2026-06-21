# Demo Script

Use this walkthrough for a portfolio demo or interview conversation.

## Start The Stack

Backend:

```powershell
.\.venv\Scripts\alembic.exe upgrade head
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

## Product Walkthrough

1. Register or log in.
2. Open the default workspace dashboard.
3. Upload a small TXT or Markdown document.
4. Show the ingestion job and document status.
5. Open Chat and ask a grounded question.
6. Point out citations in the answer.
7. Open the source/citation drawer to show evidence.
8. Open Review and demonstrate approval/rejection workflow if review items are
   present.
9. Open Usage and show quota progress.
10. Open Billing and show internal Free/Pro plan limits.
11. Open Settings and export workspace data.
12. Request workspace deletion only in a disposable demo workspace.
13. Log in as a platform admin.
14. Open Admin and show workspaces, failed jobs, audit events, and audit export.

## Suggested Demo Document

```txt
Refund policy allows cancellation within 14 days.
Shipping takes five business days.
Security controls require JWT authentication and audit logging.
```

Example questions:

- `What is the refund policy?`
- `How long does shipping take?`
- `What security controls are listed?`

## Interview Talking Points

Why this exists:

- Many teams need document AI that is auditable, tenant-aware, and operationally
  safe, not a one-off chatbot.

Engineering decisions:

- FastAPI keeps backend behavior explicit and testable.
- SQLAlchemy repositories keep persistence logic separate from routes.
- Workspace permission dependencies centralize tenancy enforcement.
- The local deterministic RAG pipeline keeps demos and CI independent of paid
  providers.
- Audit events, usage metering, billing plans, admin views, and compliance
  lifecycle controls make the system feel like a real SaaS platform.

Tradeoffs:

- The vector store is in-memory for now.
- The LLM and embedder are local deterministic adapters.
- Upload storage is local by default.
- Soft deletion exists, but permanent deletion is future work.
- Stripe, SSO/SAML, SCIM, and object storage are intentionally not included.

What to improve next:

- Durable vector database.
- Background ingestion worker.
- External LLM/embedding provider adapters.
- Object storage.
- Stripe-backed billing lifecycle.
- Permanent deletion worker and retention scheduler.
- Stronger CSP and SSO/SCIM for enterprise customers.
