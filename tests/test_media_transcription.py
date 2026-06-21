from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.answers.types import AnswerSource
from app.db.models import IngestionJob
from app.ingestion.loader import detect_input_type, load_document
from app.ingestion.transcribe import (
    TranscriptionError,
    TranscriptResult,
    TranscriptSegment,
    format_timestamp,
    transcript_to_text_blocks,
)
from app.ingestion.types import InputType
from app.main import app
from app.repositories.documents import DocumentRepository
from app.routes.query import _source_response
from app.routes.upload import get_media_worker
from app.storage.artifacts import ArtifactStorage
from tests.helpers import create_authenticated_workspace


class FakeAudioExtractor:
    def __init__(self) -> None:
        self.calls: list[tuple[Path, Path]] = []

    def extract_audio(self, input_path: Path, output_path: Path) -> Path:
        self.calls.append((input_path, output_path))
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(b"fake wav")
        return output_path


class FakeTranscriber:
    def __init__(self) -> None:
        self.calls: list[Path] = []

    def transcribe(self, audio_path: Path) -> TranscriptResult:
        self.calls.append(audio_path)
        return TranscriptResult(
            text="Refund policy allows cancellation within fourteen days.",
            language="en",
            duration_seconds=30.0,
            segments=[
                TranscriptSegment(
                    index=0,
                    text="Refund policy allows cancellation within fourteen days.",
                    start_seconds=1.0,
                    end_seconds=6.0,
                    confidence=0.92,
                )
            ],
        )


class FakeMediaWorker:
    def __init__(self, should_fail: bool = False) -> None:
        self.should_fail = should_fail
        self.calls: list[tuple[str, str, Path]] = []

    def process_media(
        self,
        workspace_id: str,
        document_id: str,
        input_path: Path,
    ):
        self.calls.append((workspace_id, document_id, input_path))

        if self.should_fail:
            raise TranscriptionError("Media transcription failed clearly.")

        return transcript_to_text_blocks(
            TranscriptResult(
                text="Refund policy allows cancellation within fourteen days.",
                language="en",
                duration_seconds=30.0,
                segments=[
                    TranscriptSegment(
                        index=0,
                        text="Refund policy allows cancellation within fourteen days.",
                        start_seconds=1.0,
                        end_seconds=6.0,
                        confidence=0.92,
                    )
                ],
            ),
            source_type="audio",
        )


def test_format_timestamp() -> None:
    assert format_timestamp(0) == "00:00:00"
    assert format_timestamp(72) == "00:01:12"
    assert format_timestamp(3723) == "01:02:03"


def test_transcript_converts_to_text_blocks_with_timestamp_metadata() -> None:
    result = TranscriptResult(
        text="First segment. Second segment.",
        language="en",
        duration_seconds=75.0,
        segments=[
            TranscriptSegment(
                index=0,
                text="First segment.",
                start_seconds=0.0,
                end_seconds=20.0,
                confidence=0.9,
            ),
            TranscriptSegment(
                index=1,
                text="Second segment.",
                start_seconds=65.0,
                end_seconds=75.0,
                confidence=0.88,
            ),
        ],
    )

    blocks = transcript_to_text_blocks(
        result,
        source_type="video",
        segment_window_seconds=60.0,
    )

    assert len(blocks) == 2
    assert "Transcript 00:00:00-00:00:20" in blocks[0].text
    assert blocks[0].metadata["transcript"] is True
    assert blocks[0].metadata["source_type"] == "video"
    assert blocks[0].metadata["start_seconds"] == 0.0
    assert blocks[0].metadata["end_seconds"] == 20.0
    assert blocks[0].metadata["timestamp_start"] == "00:00:00"
    assert blocks[0].metadata["timestamp_end"] == "00:00:20"
    assert blocks[0].metadata["segments"][0]["confidence"] == 0.9


def test_loader_recognizes_supported_media_extensions() -> None:
    for filename in ["sample.mp3", "sample.wav", "sample.m4a", "sample.flac", "sample.ogg"]:
        assert detect_input_type(filename) == InputType.AUDIO

    for filename in ["sample.mp4", "sample.mov", "sample.mkv", "sample.webm"]:
        assert detect_input_type(filename) == InputType.VIDEO


def test_loader_routes_audio_to_transcriber(tmp_path: Path) -> None:
    audio_path = tmp_path / "sample.mp3"
    audio_path.write_bytes(b"fake mp3")
    transcriber = FakeTranscriber()

    document = load_document(
        path=audio_path,
        input_type=InputType.AUDIO,
        title="sample",
        workspace_id="workspace-media",
        document_id="document-media",
        artifact_storage=ArtifactStorage(tmp_path / "artifacts"),
        audio_extractor=FakeAudioExtractor(),
        transcriber=transcriber,
    )

    assert document.source_type == InputType.AUDIO
    assert transcriber.calls == [audio_path]
    assert document.blocks[0].metadata["source_type"] == "audio"
    assert document.blocks[0].metadata["timestamp_start"] == "00:00:01"


def test_uploading_media_creates_async_job_and_transcript_chunks(
    client: TestClient,
    db_session: Session,
) -> None:
    workspace_id, headers = create_authenticated_workspace(
        db_session,
        email="media-upload@example.com",
    )
    fake_worker = FakeMediaWorker()
    app.dependency_overrides[get_media_worker] = lambda: fake_worker

    response = client.post(
        f"/api/v1/workspaces/{workspace_id}/documents/upload",
        headers=headers,
        files={
            "file": (
                "sample.mp3",
                b"fake audio bytes",
                "audio/mpeg",
            )
        },
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["status"] == "processing"
    assert payload["chunks_created"] == 0
    assert fake_worker.calls

    document_repo = DocumentRepository(db_session)
    chunks = document_repo.list_chunks_for_document(
        workspace_id=workspace_id,
        document_id=payload["document_id"],
    )
    job = db_session.get(IngestionJob, payload["job_id"])

    assert job is not None
    assert job.status == "succeeded"
    assert len(chunks) == 1
    assert chunks[0].source_metadata["transcript"] is True
    assert chunks[0].source_metadata["timestamp_start"] == "00:00:01"


def test_failed_media_background_processing_marks_job_failed(
    client: TestClient,
    db_session: Session,
) -> None:
    workspace_id, headers = create_authenticated_workspace(
        db_session,
        email="media-failure@example.com",
    )
    app.dependency_overrides[get_media_worker] = lambda: FakeMediaWorker(should_fail=True)

    response = client.post(
        f"/api/v1/workspaces/{workspace_id}/documents/upload",
        headers=headers,
        files={
            "file": (
                "broken.mp4",
                b"fake video bytes",
                "video/mp4",
            )
        },
    )

    assert response.status_code == 201
    payload = response.json()
    job = db_session.get(IngestionJob, payload["job_id"])

    assert job is not None
    assert job.status == "failed"
    assert job.error_message == "Media transcription failed clearly."


def test_query_source_response_preserves_transcript_timestamp_metadata() -> None:
    source = AnswerSource(
        source_id="S1",
        chunk_id="chunk-1",
        document_id="document-1",
        workspace_id="workspace-1",
        text="Transcript 00:01:12-00:02:03",
        source_page=None,
        source_start_offset=0,
        source_end_offset=31,
        score=0.9,
        metadata={
            "source_type": "video",
            "transcript": True,
            "timestamp_start": "00:01:12",
            "timestamp_end": "00:02:03",
        },
    )

    response = _source_response(source)

    assert response.metadata["transcript"] is True
    assert response.metadata["timestamp_start"] == "00:01:12"
    assert response.metadata["timestamp_end"] == "00:02:03"
