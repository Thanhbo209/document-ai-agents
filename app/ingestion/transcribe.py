from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from app.ingestion.types import ExtractedTextBlock


@dataclass(frozen=True)
class TranscriptSegment:
    index: int
    text: str
    start_seconds: float
    end_seconds: float
    confidence: float | None = None


@dataclass(frozen=True)
class TranscriptResult:
    text: str
    language: str | None
    duration_seconds: float | None
    segments: list[TranscriptSegment]


class TranscriptionError(RuntimeError):
    pass


class TranscriberUnavailableError(RuntimeError):
    def __init__(self) -> None:
        super().__init__(
            "Local Whisper transcriber unavailable. Install Whisper to process media uploads."
        )


class Transcriber(Protocol):
    def transcribe(
        self,
        audio_path: Path,
    ) -> TranscriptResult: ...


class WhisperTranscriber:
    def __init__(
        self,
        model_name: str = "base",
    ) -> None:
        self.model_name = model_name
        self._model = None

    def transcribe(
        self,
        audio_path: Path,
    ) -> TranscriptResult:
        model = self._load_model()

        try:
            raw_result = model.transcribe(str(audio_path))
        except Exception as exc:
            raise TranscriptionError(f"Whisper transcription failed: {exc}") from exc

        raw_segments = raw_result.get("segments") or []
        segments = [
            TranscriptSegment(
                index=int(segment.get("id", index)),
                text=str(segment.get("text", "")).strip(),
                start_seconds=float(segment.get("start", 0.0)),
                end_seconds=float(segment.get("end", 0.0)),
                confidence=None,
            )
            for index, segment in enumerate(raw_segments)
            if str(segment.get("text", "")).strip()
        ]
        text = str(raw_result.get("text", "")).strip()
        duration = max((segment.end_seconds for segment in segments), default=None)

        return TranscriptResult(
            text=text,
            language=raw_result.get("language"),
            duration_seconds=duration,
            segments=segments,
        )

    def _load_model(self):
        if self._model is not None:
            return self._model

        try:
            import whisper
        except ImportError as exc:
            raise TranscriberUnavailableError() from exc

        try:
            self._model = whisper.load_model(self.model_name)
        except Exception as exc:
            raise TranscriberUnavailableError() from exc

        return self._model


def format_timestamp(seconds: float) -> str:
    normalized = max(0, int(seconds))
    hours, remainder = divmod(normalized, 3600)
    minutes, secs = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def transcript_to_text_blocks(
    result: TranscriptResult,
    source_type: str,
    segment_window_seconds: float = 60.0,
) -> list[ExtractedTextBlock]:
    segments = _normalized_segments(result)

    if not segments:
        return []

    grouped_segments: list[list[TranscriptSegment]] = []
    current_group: list[TranscriptSegment] = []
    current_start: float | None = None

    for segment in segments:
        if current_start is None:
            current_start = segment.start_seconds

        exceeds_window = (
            current_group and segment.end_seconds - current_start > segment_window_seconds
        )

        if exceeds_window:
            grouped_segments.append(current_group)
            current_group = []
            current_start = segment.start_seconds

        current_group.append(segment)

    if current_group:
        grouped_segments.append(current_group)

    blocks: list[ExtractedTextBlock] = []
    for group in grouped_segments:
        start_seconds = group[0].start_seconds
        end_seconds = max(segment.end_seconds for segment in group)
        timestamp_start = format_timestamp(start_seconds)
        timestamp_end = format_timestamp(end_seconds)
        transcript_text = " ".join(
            segment.text.strip() for segment in group if segment.text.strip()
        )
        block_text = f"Transcript {timestamp_start}-{timestamp_end}\n\n{transcript_text}".strip()

        metadata = {
            "source_type": source_type,
            "transcript": True,
            "start_seconds": start_seconds,
            "end_seconds": end_seconds,
            "timestamp_start": timestamp_start,
            "timestamp_end": timestamp_end,
            "language": result.language,
            "duration_seconds": result.duration_seconds,
            "segment_count": len(group),
            "segments": [
                {
                    "index": segment.index,
                    "text": segment.text,
                    "start_seconds": segment.start_seconds,
                    "end_seconds": segment.end_seconds,
                    "confidence": segment.confidence,
                }
                for segment in group
            ],
        }

        blocks.append(
            ExtractedTextBlock(
                text=block_text,
                source_page=None,
                source_start_offset=0,
                source_end_offset=len(block_text),
                metadata=metadata,
            )
        )

    return blocks


def _normalized_segments(result: TranscriptResult) -> list[TranscriptSegment]:
    segments = [
        segment
        for segment in result.segments
        if segment.text.strip() and segment.end_seconds >= segment.start_seconds
    ]

    if segments:
        return segments

    text = result.text.strip()
    if not text:
        return []

    duration = result.duration_seconds or 0.0
    return [
        TranscriptSegment(
            index=0,
            text=text,
            start_seconds=0.0,
            end_seconds=duration,
            confidence=None,
        )
    ]
