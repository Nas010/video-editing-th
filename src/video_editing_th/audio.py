"""Deterministic FFmpeg silence analysis."""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

from .errors import VideoEditingError
from .models import MediaItem, SilenceInterval

SILENCE_START_RE = re.compile(r"silence_start:\s*(?P<value>-?\d+(?:\.\d+)?)")
SILENCE_END_RE = re.compile(
    r"silence_end:\s*(?P<end>-?\d+(?:\.\d+)?)\s*\|\s*"
    r"silence_duration:\s*(?P<duration>\d+(?:\.\d+)?)"
)


def build_silencedetect_command(
    source_path: Path,
    *,
    threshold_db: float = -35,
    minimum_seconds: float = 0.15,
    ffmpeg_binary: str = "ffmpeg",
) -> list[str]:
    return [
        ffmpeg_binary,
        "-hide_banner",
        "-nostats",
        "-i",
        str(source_path),
        "-vn",
        "-af",
        f"silencedetect=noise={threshold_db:g}dB:d={minimum_seconds:g}",
        "-f",
        "null",
        "-",
        "-nostdin",
    ]


def parse_silencedetect(
    stderr: str,
    *,
    media_duration: float | None = None,
) -> list[SilenceInterval]:
    intervals: list[SilenceInterval] = []
    pending_start: float | None = None
    for line in stderr.splitlines():
        start_match = SILENCE_START_RE.search(line)
        if start_match:
            pending_start = max(0.0, float(start_match.group("value")))
            continue
        end_match = SILENCE_END_RE.search(line)
        if end_match and pending_start is not None:
            end = max(pending_start, float(end_match.group("end")))
            duration = max(0.0, float(end_match.group("duration")))
            if end > pending_start and duration > 0:
                intervals.append(
                    SilenceInterval(start=pending_start, end=end, duration=duration)
                )
            pending_start = None
    if pending_start is not None and media_duration is not None and media_duration > pending_start:
        intervals.append(
            SilenceInterval(
                start=pending_start,
                end=media_duration,
                duration=media_duration - pending_start,
            )
        )
    return intervals


def detect_silence(
    media: MediaItem,
    *,
    threshold_db: float = -35,
    minimum_seconds: float = 0.15,
    ffmpeg_binary: str = "ffmpeg",
) -> list[SilenceInterval]:
    command = build_silencedetect_command(
        media.source_path,
        threshold_db=threshold_db,
        minimum_seconds=minimum_seconds,
        ffmpeg_binary=ffmpeg_binary,
    )
    try:
        completed = subprocess.run(command, capture_output=True, text=True, check=True)
    except (OSError, subprocess.CalledProcessError) as exc:
        detail = getattr(exc, "stderr", "") or str(exc)
        raise VideoEditingError(f"FFmpeg silence analysis failed: {detail.strip()}") from exc
    return parse_silencedetect(completed.stderr, media_duration=media.duration_seconds)
