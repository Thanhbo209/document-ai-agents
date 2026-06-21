# Admin Console

The admin console is an internal support surface for platform operators. Platform
admins are separate from workspace owners: a user must have
`is_platform_admin = true` to access `/api/v1/admin/*` routes or the `/admin`
frontend page.

## What Admins Can Inspect

The console is metadata-first. Admins can inspect:

- Workspace name, ID, owner user ID, and owner email.
- Document metadata such as title, source type, status, file count, and chunk count.
- Ingestion job status, timestamps, and error messages.
- Usage and billing plan metadata surfaced through workspace summaries.
- Audit and security events, including audit payloads.

## Private Content Boundary

Admins must not read private document content by default. The admin APIs and UI
must not expose:

- Raw uploaded file contents.
- Extracted document text.
- Chunk text.
- Conversation message content.
- Full private source content.

The document metadata endpoint intentionally returns only IDs, titles, status,
source type, timestamps, file counts, and chunk counts.

## Audit Export

`GET /api/v1/admin/audit-events/export` supports `format=csv` and `format=json`.
Exports are intended for operational review and include audit event metadata and
payloads. They require a platform admin bearer token.

## Future Break-Glass Access

Break-glass access to private content is not implemented. If added later, it
should require an explicit reason, approval where appropriate, strict scoping,
and a dedicated audit event for every access.
