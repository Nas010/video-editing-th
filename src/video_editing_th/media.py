"""Source-media discovery, hashing, and FFprobe normalization."""

from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import datetime
from fractions import Fraction
from pathlib import Path
from typing import Any

from .errors import VideoEditingError
from .models import MediaItem

SUPPORTED_MEDIA_EXTENSIONS = {
    ".avi",
    ".m4a",
    ".mkv",
    ".mov",
    ".mp3",
    ".mp4",
    ".wav",
    ".webm",
}


def hash_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()


def _parse_rate(value: str | None) -> float | None:
    if not value or value in {"0/0", "N/A"}:
        return None
    try:
        return float(Fraction(value))
    except (ValueError, ZeroDivisionError):
        return None


def _parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    normalized = value.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(normalized)
    except ValueError:
        return None


def _first_stream(streams: list[dict[str, Any]], kind: str) -> dict[str, Any] | None:
    return next((stream for stream in streams if stream.get("codec_type") == kind), None)


def probe_media(path: Path, ffprobe_binary: str = "ffprobe") -> MediaItem:
    """Run FFprobe and normalize the result into a canonical media record."""

    resolved = path.expanduser().resolve(strict=True)
    command = [
        ffprobe_binary,
        "-v",
        "error",
        "-show_streams",
        "-show_format",
        "-of",
        "json",
        str(resolved),
    ]
    try:
        completed = subprocess.run(command, check=True, capture_output=True, text=True)
    except (OSError, subprocess.CalledProcessError) as exc:
        detail = getattr(exc, "stderr", "") or str(exc)
        raise VideoEditingError(f"FFprobe failed for {resolved}: {detail.strip()}") from exc
    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise VideoEditingError(f"FFprobe returned invalid JSON for {resolved}") from exc

    streams = payload.get("streams") if isinstance(payload, dict) else None
    format_data = payload.get("format") if isinstance(payload, dict) else None
    if not isinstance(streams, list) or not isinstance(format_data, dict):
        raise VideoEditingError(f"FFprobe output for {resolved} is missing streams or format")

    video_stream = _first_stream(streams, "video")
    audio_stream = _first_stream(streams, "audio")
    duration_value = format_data.get("duration", 0)
    try:
        duration = float(duration_value)
    except (TypeError, ValueError):
        duration = 0.0

    tags: dict[str, Any] = {}
    format_tags = format_data.get("tags")
    if isinstance(format_tags, dict):
        tags.update(format_tags)
    if video_stream and isinstance(video_stream.get("tags"), dict):
        tags.update(video_stream["tags"])

    return MediaItem(
        source_path=resolved,
        sha256=hash_file(resolved),
        size_bytes=resolved.stat().st_size,
        duration_seconds=max(duration, 0.0),
        width=video_stream.get("width") if video_stream else None,
        height=video_stream.get("height") if video_stream else None,
        fps=_parse_rate(video_stream.get("avg_frame_rate") if video_stream else None),
        has_video=video_stream is not None,
        has_audio=audio_stream is not None,
        video_codec=video_stream.get("codec_name") if video_stream else None,
        audio_codec=audio_stream.get("codec_name") if audio_stream else None,
        created_at_source=_parse_datetime(tags.get("creation_time")),
    )


def inventory_folder(
    root: Path,
    *,
    ffprobe_binary: str = "ffprobe",
    edit_dir_name: str = "edit",
) -> list[MediaItem]:
    """Inventory supported media while excluding generated project output."""

    resolved_root = root.expanduser().resolve(strict=True)
    candidates: list[Path] = []
    for candidate in resolved_root.rglob("*"):
        if not candidate.is_file() or candidate.suffix.lower() not in SUPPORTED_MEDIA_EXTENSIONS:
            continue
        relative_parts = candidate.relative_to(resolved_root).parts
        if relative_parts and relative_parts[0] == edit_dir_name:
            continue
        candidates.append(candidate)
    candidates.sort(key=lambda item: item.relative_to(resolved_root).as_posix().casefold())
    return [probe_media(candidate, ffprobe_binary=ffprobe_binary) for candidate in candidates]
