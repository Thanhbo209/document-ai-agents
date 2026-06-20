from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.repositories.documents import DocumentRepository
from app.repositories.workspaces import WorkspaceRepository


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


def create_workspace(db_session: Session) -> str:
    workspace_repo = WorkspaceRepository(db_session)

    user = workspace_repo.create_user(
        email="owner@example.com",
        display_name="Owner",
    )
    workspace = workspace_repo.create_workspace(
        name="Test Workspace",
        owner_user_id=user.id,
    )
    db_session.commit()

    return workspace.id


def test_upload_text_file_creates_document_job_file_and_chunk(
    client: TestClient,
    db_session: Session,
) -> None:
    workspace_id = create_workspace(db_session)

    response = client.post(
        f"/api/v1/workspaces/{workspace_id}/documents/upload",
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


def test_upload_markdown_file_is_accepted(
    client: TestClient,
    db_session: Session,
) -> None:
    workspace_id = create_workspace(db_session)

    response = client.post(
        f"/api/v1/workspaces/{workspace_id}/documents/upload",
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
    workspace_id = create_workspace(db_session)
    pdf_bytes = build_minimal_pdf("Hello PDF")

    response = client.post(
        f"/api/v1/workspaces/{workspace_id}/documents/upload",
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
    workspace_id = create_workspace(db_session)

    response = client.post(
        f"/api/v1/workspaces/{workspace_id}/documents/upload",
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


def test_upload_to_missing_workspace_returns_404(client: TestClient) -> None:
    response = client.post(
        "/api/v1/workspaces/missing-workspace/documents/upload",
        files={
            "file": (
                "notes.txt",
                b"Hello",
                "text/plain",
            )
        },
    )

    assert response.status_code == 404
