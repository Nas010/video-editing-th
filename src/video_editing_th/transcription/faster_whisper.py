"""Optional faster-whisper transcription backend."""

from __future__ import annotations

import math
from collections.abc import Callable
from typing import Any

from ..errors import VideoEditingError
from ..models import MediaItem, Transcript, TranscriptSegment, TranscriptWord
from .base import TranscriptionOptions

ModelFactory = Callable[..., Any]


class FasterWhisperBackend:
    name = "faster-whisper"

    def __init__(
        self,
        model_name: str = "large-v3",
        *,
        device: str = "cpu",
        compute_type: str = "int8",
        model_factory: ModelFactory | None = None,
    ) -> None:
        self.model_name = model_name
        self.device = device
        self.compute_type = compute_type
        self._model_factory = model_factory

    def _load_model(self) -> Any:
        if self._model_factory is not None:
            return self._model_factory(
                self.model_name,
                device=self.device,
                compute_type=self.compute_type,
            )
        try:
            from faster_whisper import WhisperModel
        except ImportError as exc:
            raise VideoEditingError(
                "faster-whisper is not installed; install the transcription extra"
            ) from exc
        return WhisperModel(
            self.model_name,
            device=self.device,
            compute_type=self.compute_type,
        )

    def transcribe(self, media: MediaItem, options: TranscriptionOptions) -> Transcript:
        model = self._load_model()
        segments_iter, info = model.transcribe(
            str(media.source_path),
            language=options.language,
            task="transcribe",
            word_timestamps=options.word_timestamps,
            vad_filter=options.vad_filter,
            vad_parameters={"min_silence_duration_ms": options.minimum_silence_ms},
            condition_on_previous_text=False,
            initial_prompt=options.prompt,
            beam_size=5,
        )
        words: list[TranscriptWord] = []
        segments: list[TranscriptSegment] = []
        for segment_index, raw_segment in enumerate(segments_iter):
            word_indices: list[int] = []
            for raw_word in getattr(raw_segment, "words", None) or []:
                text = str(getattr(raw_word, "word", "")).strip()
                start = float(getattr(raw_word, "start", 0) or 0)
                end = float(getattr(raw_word, "end", start) or start)
                if not text or end <= start:
                    continue
                word_indices.append(len(words))
                words.append(
                    TranscriptWord(
                        text=text,
                        start=start,
                        end=end,
                        probability=_probability(getattr(raw_word, "probability", None)),
                    )
                )
            start = float(getattr(raw_segment, "start", 0))
            end = float(getattr(raw_segment, "end", start))
            text = str(getattr(raw_segment, "text", "")).strip()
            if not word_indices and text and end > start:
                word_indices.append(len(words))
                words.append(TranscriptWord(text=text, start=start, end=end))
            if end <= start:
                continue
            avg_logprob = getattr(raw_segment, "avg_logprob", None)
            confidence = None
            if avg_logprob is not None:
                confidence = max(0.0, min(1.0, math.exp(float(avg_logprob))))
            segments.append(
                TranscriptSegment(
                    id=f"s{segment_index}",
                    start=start,
                    end=end,
                    text=text,
                    word_indices=word_indices,
                    confidence=confidence,
                    no_speech_probability=_probability(
                        getattr(raw_segment, "no_speech_prob", None)
                    ),
                )
            )
        language = str(getattr(info, "language", options.language)).lower()
        return Transcript(
            media_sha256=media.sha256,
            source_path=media.source_path,
            language=language,
            backend="faster-whisper",
            model=self.model_name,
            words=words,
            segments=segments,
        )


def _probability(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return max(0.0, min(1.0, float(value)))
    except (TypeError, ValueError):
        return None
