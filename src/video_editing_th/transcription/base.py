"""Shared transcription backend contract."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from ..models import MediaItem, Transcript


@dataclass(frozen=True, slots=True)
class TranscriptionOptions:
    """Provider-independent transcription settings."""

    language: str = "th"
    prompt: str | None = None
    word_timestamps: bool = True
    vad_filter: bool = True
    minimum_silence_ms: int = 500


@runtime_checkable
class TranscriptionBackend(Protocol):
    """Normalize an ASR provider into the canonical transcript model."""

    name: str

    def transcribe(self, media: MediaItem, options: TranscriptionOptions) -> Transcript: ...
