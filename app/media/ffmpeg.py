import subprocess
from pathlib import Path
from typing import Protocol

AUDIO_EXTENSIONS = {".flac", ".m4a", ".mp3", ".ogg", ".wav"}
VIDEO_EXTENSIONS = {".mkv", ".mov", ".mp4", ".webm"}


class FFmpegUnavailableError(RuntimeError):
    def __init__(self) -> None:
        super().__init__("FFmpeg unavailable. Install FFmpeg to process media uploads.")


class AudioExtractionError(RuntimeError):
    pass


class AudioExtractor(Protocol):
    def extract_audio(
        self,
        input_path: Path,
        output_path: Path,
    ) -> Path: ...


class FFmpegAudioExtractor:
    def extract_audio(
        self,
        input_path: Path,
        output_path: Path,
    ) -> Path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        command = [
            "ffmpeg",
            "-y",
            "-i",
            str(input_path),
            "-vn",
            "-acodec",
            "pcm_s16le",
            "-ar",
            "16000",
            "-ac",
            "1",
            str(output_path),
        ]

        try:
            result = subprocess.run(
                command,
                capture_output=True,
                check=False,
                text=True,
            )
        except FileNotFoundError as exc:
            raise FFmpegUnavailableError() from exc

        if result.returncode != 0:
            stderr = result.stderr.strip()
            message = stderr[-500:] if stderr else "FFmpeg could not extract audio."
            raise AudioExtractionError(message)

        if not output_path.exists() or output_path.stat().st_size == 0:
            raise AudioExtractionError("FFmpeg produced an empty audio artifact.")

        return output_path


def is_audio_file(path: Path) -> bool:
    return path.suffix.lower() in AUDIO_EXTENSIONS


def is_video_file(path: Path) -> bool:
    return path.suffix.lower() in VIDEO_EXTENSIONS


def is_supported_media_file(path: Path) -> bool:
    return is_audio_file(path) or is_video_file(path)
