import json
from pathlib import Path

from app.ingestion.transcribe import TranscriptResult, TranscriptSegment
from app.storage.artifacts import ArtifactStorage
from app.workers.media_worker import MediaWorker


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


def test_media_worker_processes_audio_and_writes_transcript_artifact(tmp_path: Path) -> None:
    audio_path = tmp_path / "sample.mp3"
    audio_path.write_bytes(b"fake mp3")
    storage = ArtifactStorage(tmp_path / "artifacts")
    extractor = FakeAudioExtractor()
    transcriber = FakeTranscriber()

    blocks = MediaWorker(
        artifact_storage=storage,
        audio_extractor=extractor,
        transcriber=transcriber,
    ).process_media(
        workspace_id="workspace-audio",
        document_id="document-audio",
        input_path=audio_path,
    )

    assert extractor.calls == []
    assert transcriber.calls == [audio_path]
    assert blocks[0].metadata["source_type"] == "audio"
    assert blocks[0].metadata["timestamp_start"] == "00:00:01"

    transcript_path = storage.media_transcript_json_path("workspace-audio", "document-audio")
    assert transcript_path.exists()
    payload = json.loads(transcript_path.read_text(encoding="utf-8"))
    assert payload["language"] == "en"
    assert payload["segments"][0]["confidence"] == 0.92


def test_media_worker_processes_video_with_audio_extraction(tmp_path: Path) -> None:
    video_path = tmp_path / "sample.mp4"
    video_path.write_bytes(b"fake mp4")
    storage = ArtifactStorage(tmp_path / "artifacts")
    extractor = FakeAudioExtractor()
    transcriber = FakeTranscriber()

    blocks = MediaWorker(
        artifact_storage=storage,
        audio_extractor=extractor,
        transcriber=transcriber,
    ).process_media(
        workspace_id="workspace-video",
        document_id="document-video",
        input_path=video_path,
    )

    audio_path = storage.media_audio_path("workspace-video", "document-video")
    assert extractor.calls == [(video_path, audio_path)]
    assert transcriber.calls == [audio_path]
    assert audio_path.exists()
    assert blocks[0].metadata["source_type"] == "video"
    assert blocks[0].metadata["timestamp_end"] == "00:00:06"
