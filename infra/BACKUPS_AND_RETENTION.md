# Backups And Retention

Backups are required before running this stack with real workspace data.

## PostgreSQL

Back up the PostgreSQL database on a regular schedule using your hosting
platform's managed backup feature or `pg_dump`.

Minimum requirements:

- Automated daily backups.
- Point-in-time recovery when supported by the provider.
- Backup encryption at rest.
- Access controls for restore operators.
- Restore tests on a non-production database.

Example manual backup:

```powershell
docker exec rag-platform-prod-postgres pg_dump -U rag_platform rag_platform > backup.sql
```

## Upload Storage

The upload directory is mounted as the `rag_platform_uploads` Docker volume in
`docker-compose.prod.yml`. Back it up with the same care as the database because
document metadata in PostgreSQL references files in this storage.

Backups of database and uploads should be taken close together so restored
metadata and files match.

## Restore Test Checklist

- Restore PostgreSQL into an isolated environment.
- Restore upload storage into the configured upload directory.
- Run `alembic upgrade head`.
- Start the API.
- Verify `/ready`.
- Upload a new document.
- Open an existing document list.
- Run a query against restored content.

## Retention Warning

Choose a retention policy before production use. Retaining data forever can
create privacy, storage, and compliance risk.

Workspace deletion currently uses a soft-delete lifecycle status first.
Soft-deleted workspaces may still exist in application tables, upload storage,
and backups until permanent deletion tooling is implemented.

Permanent deletion is future work. Backup retention windows affect deletion
guarantees, because deleted workspace data can remain restorable from retained
database or upload-storage backups.
