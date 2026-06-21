from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.ingestion.web import WebFetchPolicy, validate_url_for_fetch
from app.ingestion.youtube import (
    YouTubeTranscript,
    YouTubeTranscriptSegment,
)
from app.main import app
from app.repositories.documents import DocumentRepository
from app.routes.connectors import get_web_page_fetcher, get_youtube_transcript_client
from tests.helpers import create_authenticated_workspace


class FakeWebFetcher:
    def fetch_url_text(self, url: str, policy: WebFetchPolicy) -> tuple[str, dict]:
        final_url = validate_url_for_fetch(url, policy)
        return (
            "Refund policy allows cancellation within fourteen days.",
            {
                "url": url,
                "final_url": final_url,
                "title": "Refund Policy",
                "content_type": "text/html",
            },
        )


class FakeYouTubeClient:
    def fetch_transcript(self, video_id: str) -> YouTubeTranscript:
        return YouTubeTranscript(
            video_id=video_id,
            title="Refund Video",
            language="en",
            segments=[
                YouTubeTranscriptSegment(
                    text="Refund policy allows cancellation within fourteen days.",
                    start_seconds=72.0,
                    duration_seconds=6.0,
                )
            ],
        )


def test_connector_ingest_requires_auth(client: TestClient, db_session: Session) -> None:
    workspace_id, _ = create_authenticated_workspace(
        db_session,
        email="connectors-auth@example.com",
    )

    response = client.post(
        f"/api/v1/workspaces/{workspace_id}/connectors/ingest",
        json={
            "source_type": "web",
            "url": "https://example.com/refunds",
        },
    )

    assert response.status_code == 401


def test_connector_ingest_requires_workspace_access(
    client: TestClient,
    db_session: Session,
) -> None:
    _, headers = create_authenticated_workspace(
        db_session,
        email="connectors-owner-a@example.com",
    )
    other_workspace_id, _ = create_authenticated_workspace(
        db_session,
        email="connectors-owner-b@example.com",
    )

    response = client.post(
        f"/api/v1/workspaces/{other_workspace_id}/connectors/ingest",
        headers=headers,
        json={
            "source_type": "web",
            "url": "https://example.com/refunds",
        },
    )

    assert response.status_code == 403


def test_ingest_web_connector_creates_document_job_and_chunks(
    client: TestClient,
    db_session: Session,
) -> None:
    workspace_id, headers = create_authenticated_workspace(
        db_session,
        email="connectors-web@example.com",
    )
    app.dependency_overrides[get_web_page_fetcher] = lambda: FakeWebFetcher()

    response = client.post(
        f"/api/v1/workspaces/{workspace_id}/connectors/ingest",
        headers=headers,
        json={
            "source_type": "web",
            "url": "https://example.com/refunds",
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
    assert chunks[0].source_metadata["source_type"] == "web"
    assert chunks[0].source_metadata["title"] == "Refund Policy"
    assert chunks[0].source_metadata["url"] == "https://example.com/refunds"


def test_ingest_youtube_connector_creates_timestamped_chunks(
    client: TestClient,
    db_session: Session,
) -> None:
    workspace_id, headers = create_authenticated_workspace(
        db_session,
        email="connectors-youtube@example.com",
    )
    app.dependency_overrides[get_youtube_transcript_client] = lambda: FakeYouTubeClient()

    response = client.post(
        f"/api/v1/workspaces/{workspace_id}/connectors/ingest",
        headers=headers,
        json={
            "source_type": "youtube",
            "url": "https://www.youtube.com/watch?v=abcDEF123_4",
        },
    )

    assert response.status_code == 201
    payload = response.json()
    chunks = DocumentRepository(db_session).list_chunks_for_document(
        workspace_id=workspace_id,
        document_id=payload["document_id"],
    )

    assert payload["status"] == "succeeded"
    assert chunks[0].source_metadata["source_type"] == "youtube"
    assert chunks[0].source_metadata["timestamp_start"] == "00:01:12"
    assert chunks[0].source_metadata["timestamp_end"] == "00:01:18"


def test_connector_ingest_rejects_unsupported_source_type(
    client: TestClient,
    db_session: Session,
) -> None:
    workspace_id, headers = create_authenticated_workspace(
        db_session,
        email="connectors-invalid@example.com",
    )

    response = client.post(
        f"/api/v1/workspaces/{workspace_id}/connectors/ingest",
        headers=headers,
        json={
            "source_type": "rss",
            "url": "https://example.com/feed.xml",
        },
    )

    assert response.status_code == 422
