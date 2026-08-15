"""Transcription backend selection."""

from __future__ import annotations

import importlib.util
import shutil
from pathlib import Path

from ..errors import VideoEditingError
from .base import TranscriptionBackend
from .faster_whisper import FasterWhisperBackend
from .imported import ImportedTranscriptBackend
from .whisper_cpp import WhisperCppBackend


def select_backend(
    name: str,
    *,
    model_path: Path | None = None,
    imported_path: Path | None = None,
    whisper_binary: str = "whisper-cli",
    ffmpeg_binary: str = "ffmpeg",
    faster_whisper_model: str = "large-v3",
) -> TranscriptionBackend:
    normalized = name.strip().lower()
    if normalized == "imported":
        if imported_path is None:
            raise ValueError("imported backend requires imported_path")
        return ImportedTranscriptBackend(imported_path)
    if normalized in {"whisper.cpp", "whisper-cpp", "cpp"}:
        if model_path is None:
            raise ValueError("whisper.cpp backend requires model_path")
        return WhisperCppBackend(
            model_path=model_path,
            binary=whisper_binary,
            ffmpeg_binary=ffmpeg_binary,
        )
    if normalized in {"faster-whisper", "faster_whisper"}:
        return FasterWhisperBackend(faster_whisper_model)
    if normalized == "auto":
        if model_path is not None and shutil.which(whisper_binary):
            return WhisperCppBackend(
                model_path=model_path,
                binary=whisper_binary,
                ffmpeg_binary=ffmpeg_binary,
            )
        if importlib.util.find_spec("faster_whisper") is not None:
            return FasterWhisperBackend(faster_whisper_model)
        raise VideoEditingError(
            "No transcription backend is available. Install whisper.cpp or faster-whisper."
        )
    raise ValueError(f"Unknown transcription backend: {name}")
