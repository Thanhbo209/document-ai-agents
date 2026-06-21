import json
from dataclasses import asdict
from pathlib import Path

from app.ingestion.transcribe import (
    Transcriber,
    TranscriptResult,
    transcript_to_text_blocks,
)
from app.ingestion.types import ExtractedTextBlock
from app.media.ffmpeg import AudioExtractor, is_audio_file, is_video_file
from app.storage.artifacts import ArtifactStorage


class MediaWorker:
    def __init__(
        self,
        artifact_storage: ArtifactStorage,
        audio_extractor: AudioExtractor,
        transcriber: Transcriber,
    ) -> None:
        self.artifact_storage = artifact_storage
        self.audio_extractor = audio_extractor
        self.transcriber = transcriber

    def process_media(
        self,
        workspace_id: str,
        document_id: str,
        input_path: Path,
    ) -> list[ExtractedTextBlock]:
        if is_video_file(input_path):
            source_type = "video"
            audio_path = self.artifact_storage.media_audio_path(workspace_id, document_id)
            transcribe_path = self.audio_extractor.extract_audio(input_path, audio_path)
        elif is_audio_file(input_path):
            source_type = "audio"
            transcribe_path = input_path
        else:
            raise ValueError(f"Unsupported media file type: {input_path.suffix}")

        result = self.transcriber.transcribe(transcribe_path)
        self._write_transcript_json(workspace_id, document_id, result)

        return transcript_to_text_blocks(result, source_type=source_type)

    def _write_transcript_json(
        self,
        workspace_id: str,
        document_id: str,
        result: TranscriptResult,
    ) -> None:
        transcript_path = self.artifact_storage.media_transcript_json_path(
            workspace_id,
            document_id,
        )
        self.artifact_storage.write_text(
            transcript_path,
            json.dumps(asdict(result), indent=2),
        )
