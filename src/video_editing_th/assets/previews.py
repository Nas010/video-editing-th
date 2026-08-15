"""Compact contact-sheet generation for inexpensive Codex visual verification."""

from __future__ import annotations

import math
import subprocess
from pathlib import Path

from ..errors import VideoEditingError


def build_contact_sheet_command(
    source_path: Path,
    destination: Path,
    *,
    duration_seconds: float,
    frame_count: int = 6,
    thumbnail_width: int = 320,
    ffmpeg_binary: str = "ffmpeg",
) -> list[str]:
    if frame_count < 1:
        raise ValueError("frame_count must be positive")
    if duration_seconds <= 0:
        raise ValueError("duration_seconds must be positive")
    columns = math.ceil(math.sqrt(frame_count))
    rows = math.ceil(frame_count / columns)
    sample_rate = frame_count / duration_seconds
    filter_chain = (
        f"fps={sample_rate:g},scale={thumbnail_width}:-2,"
        f"tile={columns}x{rows}:padding=4:margin=4"
    )
    return [
        ffmpeg_binary,
        "-y",
        "-hide_banner",
        "-loglevel",
        "error",
        "-i",
        str(source_path),
        "-vf",
        filter_chain,
        "-frames:v",
        "1",
        str(destination),
    ]


def generate_contact_sheet(
    source_path: Path,
    destination: Path,
    *,
    duration_seconds: float,
    frame_count: int = 6,
    thumbnail_width: int = 320,
    ffmpeg_binary: str = "ffmpeg",
) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    command = build_contact_sheet_command(
        source_path,
        destination,
        duration_seconds=duration_seconds,
        frame_count=frame_count,
        thumbnail_width=thumbnail_width,
        ffmpeg_binary=ffmpeg_binary,
    )
    try:
        subprocess.run(command, check=True, capture_output=True, text=True)
    except (OSError, subprocess.CalledProcessError) as exc:
        detail = getattr(exc, "stderr", "") or str(exc)
        raise VideoEditingError(f"Contact-sheet generation failed: {detail.strip()}") from exc
