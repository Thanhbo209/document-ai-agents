# Compliance Posture

This document describes product-level enterprise controls in RAG Platform. It is
not SOC 2 certification, legal compliance advice, or a substitute for a formal
security program.

## Workspace Lifecycle

Workspaces have a lifecycle status:

- `active`: normal application usage is allowed.
- `pending_deletion`: deletion has been requested and normal workspace usage is
  blocked.
- `deleted`: the workspace is soft-deleted and normal workspace usage is
  blocked.

Pending and deleted workspaces are still retained in database rows during this
phase. Platform admin/support metadata views can still inspect lifecycle
metadata for operational support, but admin views must remain metadata-only and
must not expose private document or chunk text by default.

## Data Export

Workspace owners with manage permission can export workspace data as JSON from
the workspace settings page or compliance API.

Owner exports include workspace-owned records, including document metadata,
file metadata, chunk records, conversation records, citations, review items,
audit events, usage events, and billing subscription metadata. Because this is
an owner-initiated workspace export, it may include workspace-owned content such
as document chunk text and conversation message content.

Admin/support views are different: they remain metadata-first and do not expose
raw uploaded file content, document text, chunk text, or conversation message
content by default.

## Soft Deletion

Deletion requests are soft-delete lifecycle transitions. A request sets the
workspace to `pending_deletion` and records the request time. Marking a
workspace deleted sets the status to `deleted` and records `deleted_at`.

The platform does not physically delete all related rows or uploaded files in
this phase. A future permanent deletion worker must handle full data removal,
retention policies, legal holds, and backup coordination.

## Audit Events

The compliance controls create audit events:

- `compliance.workspace_exported`
- `compliance.workspace_deletion_requested`
- `compliance.workspace_deleted`

These events are intended for operational review and tenant lifecycle
traceability.

## Security Headers

The API adds baseline security headers:

- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `Referrer-Policy: strict-origin-when-cross-origin`
- `Permissions-Policy: camera=(), microphone=(), geolocation=()`

A strict Content Security Policy is future hardening work. It should be tested
carefully against the API, frontend, and deployment environment before enabling
in production.

## Retention Limitations

Soft-deleted workspace data may remain in application tables, upload storage,
and backups. Backup retention affects deletion guarantees, so production
operators must align database and upload-storage retention windows with their
own policy requirements.

## Future Work

- Permanent deletion worker.
- Retention scheduler.
- Legal hold support.
- Break-glass admin access with explicit reason, approval, and audit logging.
- Stronger CSP.
- SSO/SAML.
- SCIM.
