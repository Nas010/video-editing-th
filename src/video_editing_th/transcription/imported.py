"""Import canonical or common external timestamped transcript JSON."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ..models import MediaItem, Transcript, TranscriptSegment, TranscriptWord
from .base import TranscriptionOptions


class ImportedTranscriptBackend:
    name = "imported"

    def __init__(self, transcript_path: Path) -> None:
        self.transcript_path = transcript_path.expanduser().resolve(strict=True)

    def transcribe(self, media: MediaItem, options: TranscriptionOptions) -> Transcript:
        payload = json.loads(self.transcript_path.read_text(encoding="utf-8"))
        if isinstance(payload, dict) and payload.get("schema_version") == 1:
            canonical = Transcript.model_validate(payload)
            return canonical.model_copy(
                update={"media_sha256": media.sha256, "source_path": media.source_path}
            )
        if not isinstance(payload, dict):
            raise ValueError("Imported transcript must be a JSON object")
        return self._from_generic(payload, media, options)

    @staticmethod
    def _from_generic(
        payload: dict[str, Any],
        media: MediaItem,
        options: TranscriptionOptions,
    ) -> Transcript:
        raw_segments = payload.get("segments", [])
        if not isinstance(raw_segments, list):
            raise ValueError("Imported transcript segments must be a list")

        words: list[TranscriptWord] = []
        segments: list[TranscriptSegment] = []
        for segment_index, raw_segment in enumerate(raw_segments):
            if not isinstance(raw_segment, dict):
                continue
            start = float(raw_segment.get("start", 0))
            end = float(raw_segment.get("end", start))
            text = str(raw_segment.get("text", "")).strip()
            word_indices: list[int] = []
            raw_words = raw_segment.get("words", [])
            if isinstance(raw_words, list):
                for raw_word in raw_words:
                    if not isinstance(raw_word, dict):
                        continue
                    word_text = str(raw_word.get("word", raw_word.get("text", ""))).strip()
                    word_start = float(raw_word.get("start", start))
                    word_end = float(raw_word.get("end", word_start))
                    if not word_text or word_end <= word_start:
                        continue
                    word_indices.append(len(words))
                    words.append(
                        TranscriptWord(
                            text=word_text,
                            start=word_start,
                            end=word_end,
                            probability=_optional_probability(
                                raw_word.get("probability", raw_word.get("confidence"))
                            ),
                            speaker=_optional_string(raw_word.get("speaker")),
                        )
                    )
            if not word_indices and text and end > start:
                word_indices.append(len(words))
                words.append(TranscriptWord(text=text, start=start, end=end))
            if end <= start:
                continue
            segments.append(
                TranscriptSegment(
                    id=str(raw_segment.get("id", f"s{segment_index}")),
                    start=start,
                    end=end,
                    text=text,
                    word_indices=word_indices,
                    confidence=_optional_probability(
                        raw_segment.get("confidence", raw_segment.get("avg_probability"))
                    ),
                    no_speech_probability=_optional_probability(
                        raw_segment.get("no_speech_probability")
                    ),
                    speaker=_optional_string(raw_segment.get("speaker")),
                )
            )

        return Transcript(
            media_sha256=media.sha256,
            source_path=media.source_path,
            language=str(payload.get("language", options.language)).lower(),
            backend="imported",
            model=str(payload.get("model", "external")),
            words=words,
            segments=segments,
        )


def _optional_probability(value: Any) -> float | None:
    if value is None:
        return None
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return max(0.0, min(1.0, parsed))


def _optional_string(value: Any) -> str | None:
    if value is None:
        return None
    return str(value)
