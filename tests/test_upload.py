from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import UsageEvent
from app.repositories.documents import DocumentRepository
from app.repositories.workspaces import WorkspaceRepository
from tests.helpers import create_authenticated_workspace


def build_minimal_pdf(text: str) -> bytes:
    escaped_text = text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
    stream = f"BT /F1 24 Tf 100 700 Td ({escaped_text}) Tj ET".encode()

    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        (
            b"<< /Type /Page /Parent 2 0 R "
            b"/Resources << /Font << /F1 4 0 R >> >> "
            b"/MediaBox [0 0 612 792] /Contents 5 0 R >>"
        ),
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        b"<< /Length %d >>\nstream\n%s\nendstream" % (len(stream), stream),
    ]

    output = bytearray(b"%PDF-1.4\n")
    offsets = [0]

    for index, obj in enumerate(objects, start=1):
        offsets.append(len(output))
        output.extend(f"{index} 0 obj\n".encode())
        output.extend(obj)
        output.extend(b"\nendobj\n")

    xref_position = len(output)
    output.extend(f"xref\n0 {len(objects) + 1}\n".encode())
    output.extend(b"0000000000 65535 f \n")

    for offset in offsets[1:]:
        output.extend(f"{offset:010d} 00000 n \n".encode())

    output.extend(
        (
            f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\n"
            f"startxref\n{xref_position}\n%%EOF\n"
        ).encode()
    )

    return bytes(output)


def create_workspace(db_session: Session) -> tuple[str, dict[str, str]]:
    return create_authenticated_workspace(
        db_session,
        email="owner@example.com",
    )


def test_upload_text_file_creates_document_job_file_and_chunk(
    client: TestClient,
    db_session: Session,
) -> None:
    workspace_id, headers = create_workspace(db_session)

    response = client.post(
        f"/api/v1/workspaces/{workspace_id}/documents/upload",
        headers=headers,
        files={
            "file": (
                "notes.txt",
                b"Hello from text ingestion.",
                "text/plain",
            )
        },
    )

    assert response.status_code == 201

    payload = response.json()
    assert payload["document_id"]
    assert payload["file_id"]
    assert payload["job_id"]
    assert payload["status"] == "succeeded"
    assert payload["chunks_created"] == 1

    document_repo = DocumentRepository(db_session)
    chunks = document_repo.list_chunks_for_document(
        workspace_id=workspace_id,
        document_id=payload["document_id"],
    )

    assert len(chunks) == 1
    assert chunks[0].text == "Hello from text ingestion."
    assert chunks[0].source_start_offset == 0
    assert chunks[0].source_end_offset == len("Hello from text ingestion.")
    assert chunks[0].source_metadata["source_type"] == "text"


def test_upload_records_usage_metrics(
    client: TestClient,
    db_session: Session,
) -> None:
    workspace_id, headers = create_workspace(db_session)
    file_bytes = b"Hello from metered upload."

    response = client.post(
        f"/api/v1/workspaces/{workspace_id}/documents/upload",
        headers=headers,
        files={
            "file": (
                "metered.txt",
                file_bytes,
                "text/plain",
            )
        },
    )

    assert response.status_code == 201

    payload = response.json()
    document_repo = DocumentRepository(db_session)
    chunks = document_repo.list_chunks_for_document(
        workspace_id=workspace_id,
        document_id=payload["document_id"],
    )
    user = WorkspaceRepository(db_session).get_user_by_email("owner@example.com")

    usage_events = list(
        db_session.scalars(
            select(UsageEvent)
            .where(UsageEvent.workspace_id == workspace_id)
            .order_by(UsageEvent.metric_name)
        ).all()
    )
    usage_by_metric = {event.metric_name: event for event in usage_events}

    assert set(usage_by_metric) == {
        "chunk.count",
        "chunk.tokens",
        "document.count",
        "upload.bytes",
    }
    assert usage_by_metric["upload.bytes"].quantity == len(file_bytes)
    assert usage_by_metric["upload.bytes"].unit == "bytes"
    assert usage_by_metric["upload.bytes"].usage_metadata == {"filename": "metered.txt"}
    assert usage_by_metric["document.count"].quantity == 1
    assert usage_by_metric["chunk.count"].quantity == len(chunks)
    assert usage_by_metric["chunk.tokens"].quantity == sum(chunk.token_count for chunk in chunks)
    assert {event.source_id for event in usage_events} == {payload["document_id"]}
    assert {event.actor_user_id for event in usage_events} == {user.id}


def test_upload_returns_429_when_quota_is_exceeded(
    client: TestClient,
    db_session: Session,
) -> None:
    workspace_id, headers = create_workspace(db_session)
    document_repo = DocumentRepository(db_session)
    existing_document = document_repo.create_document(
        workspace_id=workspace_id,
        title="Existing storage",
        source_type="text",
    )
    document_repo.create_document_file(
        workspace_id=workspace_id,
        document_id=existing_document.id,
        filename="existing.txt",
        content_type="text/plain",
        size_bytes=100 * 1024 * 1024,
        storage_key="existing.txt",
        checksum_sha256="checksum",
    )
    db_session.commit()

    response = client.post(
        f"/api/v1/workspaces/{workspace_id}/documents/upload",
        headers=headers,
        files={
            "file": (
                "too-large-for-quota.txt",
                b"too large",
                "text/plain",
            )
        },
    )

    assert response.status_code == 429
    assert response.json()["detail"]["metric_name"] == "storage.bytes"
    assert len(DocumentRepository(db_session).list_documents_for_workspace(workspace_id)) == 1


def test_upload_markdown_file_is_accepted(
    client: TestClient,
    db_session: Session,
) -> None:
    workspace_id, headers = create_workspace(db_session)

    response = client.post(
        f"/api/v1/workspaces/{workspace_id}/documents/upload",
        headers=headers,
        files={
            "file": (
                "README.md",
                b"# Title\n\nMarkdown body.",
                "text/markdown",
            )
        },
    )

    assert response.status_code == 201

    payload = response.json()
    assert payload["status"] == "succeeded"
    assert payload["chunks_created"] == 1


def test_upload_pdf_extracts_page_text(
    client: TestClient,
    db_session: Session,
) -> None:
    workspace_id, headers = create_workspace(db_session)
    pdf_bytes = build_minimal_pdf("Hello PDF")

    response = client.post(
        f"/api/v1/workspaces/{workspace_id}/documents/upload",
        headers=headers,
        files={
            "file": (
                "sample.pdf",
                pdf_bytes,
                "application/pdf",
            )
        },
    )

    assert response.status_code == 201

    payload = response.json()
    document_repo = DocumentRepository(db_session)
    chunks = document_repo.list_chunks_for_document(
        workspace_id=workspace_id,
        document_id=payload["document_id"],
    )

    assert len(chunks) == 1
    assert "Hello PDF" in chunks[0].text
    assert chunks[0].source_page == 1
    assert chunks[0].source_metadata["source_type"] == "pdf"
    assert chunks[0].source_metadata["page_number"] == 1


def test_upload_rejects_unsupported_file_type(
    client: TestClient,
    db_session: Session,
) -> None:
    workspace_id, headers = create_workspace(db_session)

    response = client.post(
        f"/api/v1/workspaces/{workspace_id}/documents/upload",
        headers=headers,
        files={
            "file": (
                "program.exe",
                b"fake executable",
                "application/octet-stream",
            )
        },
    )

    assert response.status_code == 400
    assert "Unsupported file type" in response.json()["detail"]


def test_upload_to_missing_workspace_returns_404(
    client: TestClient,
    db_session: Session,
) -> None:
    _, headers = create_workspace(db_session)

    response = client.post(
        "/api/v1/workspaces/missing-workspace/documents/upload",
        headers=headers,
        files={
            "file": (
                "notes.txt",
                b"Hello",
                "text/plain",
            )
        },
    )

    assert response.status_code == 404
