from pathlib import Path
from zipfile import ZipFile

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.ingestion.loader import detect_input_type
from app.ingestion.repos import (
    RepoIngestionPolicy,
    ZipTraversalError,
    detect_language_from_extension,
    extract_repo_zip_blocks,
    should_ingest_repo_file,
    validate_zip_member_path,
)
from app.ingestion.types import InputType
from app.repositories.documents import DocumentRepository
from tests.helpers import create_authenticated_workspace


def test_validate_zip_member_path_blocks_traversal() -> None:
    for member_name in [
        "../evil.py",
        "/absolute/path.py",
        r"C:\evil.py",
        "safe/../../evil.py",
    ]:
        with pytest.raises(ZipTraversalError):
            validate_zip_member_path(member_name)

    assert validate_zip_member_path("src/main.py") == "src/main.py"


def test_should_ingest_repo_file_respects_filters() -> None:
    policy = RepoIngestionPolicy()

    assert should_ingest_repo_file("src/main.py", policy)
    assert should_ingest_repo_file("src/app.ts", policy)
    assert should_ingest_repo_file("README.md", policy)
    assert not should_ingest_repo_file(".env", policy)
    assert not should_ingest_repo_file("node_modules/pkg/index.js", policy)
    assert not should_ingest_repo_file(".git/config", policy)
    assert not should_ingest_repo_file("src/image.png", policy)
    assert not should_ingest_repo_file("package-lock.json", policy)


def test_extract_repo_zip_blocks_preserves_file_and_line_metadata(tmp_path: Path) -> None:
    zip_path = tmp_path / "repo.zip"
    with ZipFile(zip_path, "w") as archive:
        archive.writestr("project-main/src/main.py", "print('hello')\nprint('world')\n")
        archive.writestr("project-main/src/app.ts", "export const ok = true;\n")
        archive.writestr("project-main/README.md", "# Project\n\nDocumentation\n")
        archive.writestr("project-main/.env", "SECRET=value\n")
        archive.writestr("project-main/node_modules/pkg/index.js", "ignored\n")
        archive.writestr("project-main/src/blob.py", b"\x00\x01binary")
        archive.writestr("project-main/large.py", "x = 1\n" * 20)

    blocks = extract_repo_zip_blocks(
        zip_path,
        repo_name="project-main",
        policy=RepoIngestionPolicy(max_file_bytes=50),
    )

    file_paths = {block.metadata["file_path"] for block in blocks}
    assert "src/main.py" in file_paths
    assert "src/app.ts" in file_paths
    assert "README.md" in file_paths
    assert ".env" not in file_paths
    assert "node_modules/pkg/index.js" not in file_paths
    assert "src/blob.py" not in file_paths
    assert "large.py" not in file_paths

    main_block = next(block for block in blocks if block.metadata["file_path"] == "src/main.py")
    assert main_block.metadata["source_type"] == "repo"
    assert main_block.metadata["repo_name"] == "project-main"
    assert main_block.metadata["language"] == "python"
    assert main_block.metadata["line_start"] == 1
    assert main_block.metadata["line_end"] == 2
    assert "File: src/main.py" in main_block.text
    assert "Lines: 1-2" in main_block.text


def test_extract_repo_zip_blocks_rejects_malicious_member(tmp_path: Path) -> None:
    zip_path = tmp_path / "malicious.zip"
    with ZipFile(zip_path, "w") as archive:
        archive.writestr("src/main.py", "print('safe')\n")
        archive.writestr("../evil.py", "print('evil')\n")

    with pytest.raises(ZipTraversalError):
        extract_repo_zip_blocks(zip_path)


def test_detect_language_from_extension() -> None:
    assert detect_language_from_extension("src/main.py") == "python"
    assert detect_language_from_extension("src/app.ts") == "typescript"
    assert detect_language_from_extension("src/app.tsx") == "typescript-react"
    assert detect_language_from_extension("schema.sql") == "sql"
    assert detect_language_from_extension("unknown.bin") is None


def test_loader_recognizes_repo_zip_extension() -> None:
    assert detect_input_type("repo.zip") == InputType.REPO


def test_upload_repo_zip_succeeds_and_creates_chunks(
    client: TestClient,
    db_session: Session,
    tmp_path: Path,
) -> None:
    workspace_id, headers = create_authenticated_workspace(
        db_session,
        email="repo-upload@example.com",
    )
    zip_path = tmp_path / "repo.zip"

    with ZipFile(zip_path, "w") as archive:
        archive.writestr("repo-main/src/main.py", "print('hello from repo')\n")
        archive.writestr("repo-main/.env", "SECRET=value\n")

    response = client.post(
        f"/api/v1/workspaces/{workspace_id}/documents/upload",
        headers=headers,
        files={
            "file": (
                "repo.zip",
                zip_path.read_bytes(),
                "application/zip",
            )
        },
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["status"] == "succeeded"
    assert payload["chunks_created"] == 1

    chunks = DocumentRepository(db_session).list_chunks_for_document(
        workspace_id=workspace_id,
        document_id=payload["document_id"],
    )
    assert chunks[0].source_metadata["source_type"] == "repo"
    assert chunks[0].source_metadata["file_path"] == "src/main.py"
    assert "SECRET" not in chunks[0].text
