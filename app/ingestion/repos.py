from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from zipfile import BadZipFile, ZipFile, ZipInfo

from app.ingestion.types import ExtractedTextBlock


class RepoIngestionError(RuntimeError):
    pass


class ZipTraversalError(RepoIngestionError):
    pass


class RepoFileSkippedError(RepoIngestionError):
    pass


@dataclass(frozen=True)
class RepoIngestionPolicy:
    max_files: int = 500
    max_file_bytes: int = 500_000
    max_total_bytes: int = 20_000_000
    include_extensions: tuple[str, ...] = (
        ".py",
        ".ts",
        ".tsx",
        ".js",
        ".jsx",
        ".md",
        ".txt",
        ".json",
        ".yml",
        ".yaml",
        ".toml",
        ".sql",
        ".html",
        ".css",
    )
    exclude_dirs: tuple[str, ...] = (
        ".git",
        "node_modules",
        ".next",
        "dist",
        "build",
        "__pycache__",
        ".venv",
        "venv",
        ".pytest_cache",
        ".ruff_cache",
    )
    exclude_file_names: tuple[str, ...] = (
        ".env",
        ".env.local",
        ".env.production",
        "id_rsa",
        "id_ed25519",
        "package-lock.json",
        "pnpm-lock.yaml",
        "yarn.lock",
        "poetry.lock",
    )
    line_window: int = 120
    line_overlap: int = 10


DEFAULT_REPO_INGESTION_POLICY = RepoIngestionPolicy()
_WINDOWS_DRIVE_PATTERN = re.compile(r"^[A-Za-z]:")
_LANGUAGES_BY_EXTENSION = {
    ".css": "css",
    ".html": "html",
    ".js": "javascript",
    ".jsx": "javascript-react",
    ".json": "json",
    ".md": "markdown",
    ".py": "python",
    ".sql": "sql",
    ".toml": "toml",
    ".ts": "typescript",
    ".tsx": "typescript-react",
    ".txt": "text",
    ".yaml": "yaml",
    ".yml": "yaml",
}


def validate_zip_member_path(member_name: str) -> str:
    if "\x00" in member_name:
        raise ZipTraversalError("ZIP member path contains a null byte.")

    if _WINDOWS_DRIVE_PATTERN.match(member_name):
        raise ZipTraversalError("ZIP member path contains a Windows drive prefix.")

    normalized = member_name.replace("\\", "/")

    if normalized.startswith("/") or normalized.startswith("//"):
        raise ZipTraversalError("ZIP member path must be relative.")

    parts = [part for part in PurePosixPath(normalized).parts if part not in {"", "."}]

    if not parts:
        raise ZipTraversalError("ZIP member path is empty.")

    if any(part == ".." for part in parts):
        raise ZipTraversalError("ZIP member path contains traversal.")

    return "/".join(parts)


def should_ingest_repo_file(path: str, policy: RepoIngestionPolicy) -> bool:
    safe_path = validate_zip_member_path(path)
    parts = safe_path.split("/")
    filename = parts[-1]
    suffix = Path(filename).suffix.lower()

    if any(part in policy.exclude_dirs for part in parts[:-1]):
        return False

    if filename in policy.exclude_file_names:
        return False

    return suffix in policy.include_extensions


def extract_repo_zip_blocks(
    zip_path: Path,
    repo_name: str | None = None,
    policy: RepoIngestionPolicy | None = None,
) -> list[ExtractedTextBlock]:
    active_policy = policy or DEFAULT_REPO_INGESTION_POLICY

    try:
        with ZipFile(zip_path) as archive:
            safe_members = _validated_members(archive)
            common_root = _common_root(safe_members)
            blocks = _extract_safe_members(
                archive=archive,
                safe_members=safe_members,
                common_root=common_root,
                repo_name=repo_name or zip_path.stem,
                policy=active_policy,
            )
    except BadZipFile as exc:
        raise RepoIngestionError(f"Could not open repository ZIP: {exc}") from exc

    if not blocks:
        raise RepoIngestionError("Repository ZIP did not contain supported text files.")

    return blocks


def detect_language_from_extension(path: str) -> str | None:
    return _LANGUAGES_BY_EXTENSION.get(Path(path).suffix.lower())


def _validated_members(archive: ZipFile) -> list[tuple[ZipInfo, str]]:
    safe_members: list[tuple[ZipInfo, str]] = []

    for member in archive.infolist():
        safe_path = validate_zip_member_path(member.filename)
        safe_members.append((member, safe_path))

    return safe_members


def _extract_safe_members(
    archive: ZipFile,
    safe_members: list[tuple[ZipInfo, str]],
    common_root: str | None,
    repo_name: str,
    policy: RepoIngestionPolicy,
) -> list[ExtractedTextBlock]:
    blocks: list[ExtractedTextBlock] = []
    ingested_files = 0
    total_bytes = 0

    for member, safe_path in safe_members:
        if member.is_dir():
            continue

        display_path = _strip_common_root(safe_path, common_root)

        if not should_ingest_repo_file(display_path, policy):
            continue

        if member.file_size > policy.max_file_bytes:
            continue

        if ingested_files >= policy.max_files:
            break

        total_bytes += member.file_size
        if total_bytes > policy.max_total_bytes:
            break

        raw = archive.read(member)
        if _looks_binary(raw):
            continue

        text = raw.decode("utf-8", errors="replace")
        if not text.strip():
            continue

        blocks.extend(
            _file_text_to_blocks(
                repo_name=repo_name,
                file_path=display_path,
                text=text,
                policy=policy,
            )
        )
        ingested_files += 1

    return blocks


def _file_text_to_blocks(
    repo_name: str,
    file_path: str,
    text: str,
    policy: RepoIngestionPolicy,
) -> list[ExtractedTextBlock]:
    lines = text.splitlines()
    if not lines:
        return []

    blocks: list[ExtractedTextBlock] = []
    start_index = 0
    language = detect_language_from_extension(file_path)

    while start_index < len(lines):
        end_index = min(start_index + policy.line_window, len(lines))
        line_start = start_index + 1
        line_end = end_index
        window_text = "\n".join(lines[start_index:end_index])
        block_text = f"File: {file_path}\nLines: {line_start}-{line_end}\n\n{window_text}"
        metadata = {
            "source_type": "repo",
            "repo_name": repo_name,
            "file_path": file_path,
            "language": language,
            "line_start": line_start,
            "line_end": line_end,
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

        if end_index == len(lines):
            break

        next_start = end_index - policy.line_overlap
        start_index = next_start if next_start > start_index else end_index

    return blocks


def _looks_binary(raw: bytes) -> bool:
    if b"\x00" in raw:
        return True

    sample = raw[:1024]
    if not sample:
        return False

    control_count = sum(1 for byte in sample if byte < 9 or (13 < byte < 32))
    return control_count / len(sample) > 0.20


def _common_root(safe_members: list[tuple[ZipInfo, str]]) -> str | None:
    top_levels = {
        path.split("/", 1)[0]
        for member, path in safe_members
        if not member.is_dir() and "/" in path
    }

    if len(top_levels) == 1:
        return next(iter(top_levels))

    return None


def _strip_common_root(path: str, common_root: str | None) -> str:
    if common_root and path.startswith(f"{common_root}/"):
        return path[len(common_root) + 1 :]

    return path
