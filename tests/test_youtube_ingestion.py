import sys
from types import SimpleNamespace

import pytest

from app.ingestion.youtube import (
    YouTubeTranscript,
    YouTubeTranscriptApiClient,
    YouTubeTranscriptError,
    YouTubeTranscriptSegment,
    extract_youtube_blocks,
    extract_youtube_video_id,
    youtube_transcript_to_blocks,
)


class FakeYouTubeClient:
    def fetch_transcript(self, video_id: str) -> YouTubeTranscript:
        return YouTubeTranscript(
            video_id=video_id,
            title="Refund Policy Walkthrough",
            language="en",
            segments=[
                YouTubeTranscriptSegment(
                    text="The refund policy allows cancellation.",
                    start_seconds=12.0,
                    duration_seconds=10.0,
                ),
                YouTubeTranscriptSegment(
                    text="Customers have fourteen days to request it.",
                    start_seconds=75.0,
                    duration_seconds=8.0,
                ),
            ],
        )


class FailingYouTubeClient:
    def fetch_transcript(self, video_id: str) -> YouTubeTranscript:
        raise YouTubeTranscriptError(f"Transcript unavailable for {video_id}.")


def test_extract_youtube_video_id_supports_common_formats() -> None:
    assert extract_youtube_video_id("abcDEF123_4") == "abcDEF123_4"
    assert extract_youtube_video_id("https://www.youtube.com/watch?v=abcDEF123_4") == "abcDEF123_4"
    assert extract_youtube_video_id("https://youtu.be/abcDEF123_4") == "abcDEF123_4"
    assert extract_youtube_video_id("https://www.youtube.com/shorts/abcDEF123_4") == "abcDEF123_4"


def test_extract_youtube_video_id_rejects_invalid_values() -> None:
    with pytest.raises(YouTubeTranscriptError, match="Invalid YouTube"):
        extract_youtube_video_id("https://example.com/not-youtube")


def test_youtube_transcript_to_blocks_groups_timestamp_windows() -> None:
    transcript = FakeYouTubeClient().fetch_transcript("abcDEF123_4")

    blocks = youtube_transcript_to_blocks(
        transcript,
        segment_window_seconds=60.0,
    )

    assert len(blocks) == 2
    assert "YouTube Transcript 00:00:12-00:00:22" in blocks[0].text
    assert blocks[0].metadata["source_type"] == "youtube"
    assert blocks[0].metadata["video_id"] == "abcDEF123_4"
    assert blocks[0].metadata["timestamp_start"] == "00:00:12"
    assert blocks[0].metadata["timestamp_end"] == "00:00:22"
    assert blocks[1].metadata["timestamp_start"] == "00:01:15"


def test_extract_youtube_blocks_uses_fake_client() -> None:
    blocks = extract_youtube_blocks(
        url_or_id="https://www.youtube.com/watch?v=abcDEF123_4",
        client=FakeYouTubeClient(),
    )

    assert len(blocks) == 2
    assert blocks[0].metadata["title"] == "Refund Policy Walkthrough"
    assert "cancellation" in blocks[0].text


def test_transcript_unavailable_error_is_readable() -> None:
    with pytest.raises(YouTubeTranscriptError, match="Transcript unavailable"):
        extract_youtube_blocks("abcDEF123_4", FailingYouTubeClient())


def test_youtube_api_client_supports_current_fetch_api(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeFetchedTranscript:
        language_code = "en"

        def to_raw_data(self) -> list[dict]:
            return [
                {
                    "text": "Transcript from the current package API.",
                    "start": 3.0,
                    "duration": 4.0,
                }
            ]

    class FakeYouTubeTranscriptApi:
        def fetch(self, video_id: str) -> FakeFetchedTranscript:
            assert video_id == "abcDEF123_4"
            return FakeFetchedTranscript()

    monkeypatch.setitem(
        sys.modules,
        "youtube_transcript_api",
        SimpleNamespace(YouTubeTranscriptApi=FakeYouTubeTranscriptApi),
    )

    transcript = YouTubeTranscriptApiClient().fetch_transcript("abcDEF123_4")

    assert transcript.language == "en"
    assert transcript.segments[0].text == "Transcript from the current package API."
    assert transcript.segments[0].start_seconds == 3.0
