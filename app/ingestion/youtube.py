import re
from dataclasses import dataclass
from typing import Protocol
from urllib.parse import parse_qs, urlparse

from app.ingestion.transcribe import format_timestamp
from app.ingestion.types import ExtractedTextBlock

_VIDEO_ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]{11}$")


class YouTubeTranscriptError(RuntimeError):
    pass


@dataclass(frozen=True)
class YouTubeTranscriptSegment:
    text: str
    start_seconds: float
    duration_seconds: float


@dataclass(frozen=True)
class YouTubeTranscript:
    video_id: str
    title: str | None
    language: str | None
    segments: list[YouTubeTranscriptSegment]


class YouTubeTranscriptClient(Protocol):
    def fetch_transcript(self, video_id: str) -> YouTubeTranscript: ...


class YouTubeTranscriptApiClient:
    def fetch_transcript(self, video_id: str) -> YouTubeTranscript:
        try:
            from youtube_transcript_api import YouTubeTranscriptApi
        except ImportError as exc:
            raise YouTubeTranscriptError(
                "YouTube transcript support is unavailable. Install youtube-transcript-api."
            ) from exc

        try:
            fetched_transcript = _fetch_with_supported_api(YouTubeTranscriptApi, video_id)
        except Exception as exc:
            raise YouTubeTranscriptError(f"YouTube transcript unavailable: {exc}") from exc

        raw_transcript = _raw_transcript_items(fetched_transcript)
        segments = [
            YouTubeTranscriptSegment(
                text=str(item.get("text", "")).strip(),
                start_seconds=float(item.get("start", 0.0)),
                duration_seconds=float(item.get("duration", 0.0)),
            )
            for item in raw_transcript
            if str(item.get("text", "")).strip()
        ]

        return YouTubeTranscript(
            video_id=video_id,
            title=None,
            language=_transcript_language(fetched_transcript),
            segments=segments,
        )


def extract_youtube_video_id(url_or_id: str) -> str:
    value = url_or_id.strip()

    if _VIDEO_ID_PATTERN.match(value):
        return value

    parsed = urlparse(value)
    host = (parsed.hostname or "").lower()

    if host in {"youtube.com", "www.youtube.com", "m.youtube.com"}:
        if parsed.path == "/watch":
            video_id = parse_qs(parsed.query).get("v", [None])[0]
            if video_id and _VIDEO_ID_PATTERN.match(video_id):
                return video_id

        parts = [part for part in parsed.path.strip("/").split("/") if part]
        if (
            len(parts) >= 2
            and parts[0] in {"shorts", "embed"}
            and _VIDEO_ID_PATTERN.match(parts[1])
        ):
            return parts[1]

    if host == "youtu.be":
        video_id = parsed.path.strip("/").split("/", 1)[0]
        if _VIDEO_ID_PATTERN.match(video_id):
            return video_id

    raise YouTubeTranscriptError("Invalid YouTube video URL or ID.")


def youtube_transcript_to_blocks(
    transcript: YouTubeTranscript,
    segment_window_seconds: float = 60.0,
) -> list[ExtractedTextBlock]:
    if not transcript.segments:
        return []

    grouped_segments: list[list[YouTubeTranscriptSegment]] = []
    current_group: list[YouTubeTranscriptSegment] = []
    current_start: float | None = None

    for segment in transcript.segments:
        segment_end = segment.start_seconds + segment.duration_seconds
        if current_start is None:
            current_start = segment.start_seconds

        exceeds_window = current_group and segment_end - current_start > segment_window_seconds
        if exceeds_window:
            grouped_segments.append(current_group)
            current_group = []
            current_start = segment.start_seconds

        current_group.append(segment)

    if current_group:
        grouped_segments.append(current_group)

    blocks: list[ExtractedTextBlock] = []
    url = f"https://www.youtube.com/watch?v={transcript.video_id}"

    for group in grouped_segments:
        start_seconds = group[0].start_seconds
        end_seconds = max(segment.start_seconds + segment.duration_seconds for segment in group)
        timestamp_start = format_timestamp(start_seconds)
        timestamp_end = format_timestamp(end_seconds)
        text = " ".join(segment.text.strip() for segment in group if segment.text.strip())
        block_text = f"YouTube Transcript {timestamp_start}-{timestamp_end}\n\n{text}".strip()

        metadata = {
            "source_type": "youtube",
            "video_id": transcript.video_id,
            "url": url,
            "title": transcript.title,
            "language": transcript.language,
            "start_seconds": start_seconds,
            "end_seconds": end_seconds,
            "timestamp_start": timestamp_start,
            "timestamp_end": timestamp_end,
            "segment_count": len(group),
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


def extract_youtube_blocks(
    url_or_id: str,
    client: YouTubeTranscriptClient,
) -> list[ExtractedTextBlock]:
    video_id = extract_youtube_video_id(url_or_id)
    transcript = client.fetch_transcript(video_id)
    blocks = youtube_transcript_to_blocks(transcript)

    if not blocks:
        raise YouTubeTranscriptError("YouTube transcript did not contain readable text.")

    return blocks


def _fetch_with_supported_api(api_class: object, video_id: str) -> object:
    if hasattr(api_class, "get_transcript"):
        return api_class.get_transcript(video_id)

    api = api_class()
    if hasattr(api, "fetch"):
        return api.fetch(video_id)

    raise YouTubeTranscriptError("Unsupported youtube-transcript-api version.")


def _raw_transcript_items(fetched_transcript: object) -> list[dict]:
    if isinstance(fetched_transcript, list):
        return fetched_transcript

    if hasattr(fetched_transcript, "to_raw_data"):
        raw_data = fetched_transcript.to_raw_data()
        return list(raw_data)

    return [
        {
            "text": getattr(item, "text", ""),
            "start": getattr(item, "start", 0.0),
            "duration": getattr(item, "duration", 0.0),
        }
        for item in fetched_transcript
    ]


def _transcript_language(fetched_transcript: object) -> str | None:
    language_code = getattr(fetched_transcript, "language_code", None)
    if language_code:
        return str(language_code)

    language = getattr(fetched_transcript, "language", None)
    return str(language) if language else None
