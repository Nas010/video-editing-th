"""Local whisper.cpp adapter with explicit Thai language routing."""

from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from ..errors import VideoEditingError
from ..models import MediaItem, Transcript, TranscriptSegment, TranscriptWord
from .base import TranscriptionOptions


class WhisperCppBackend:
    name = "whisper.cpp"

    def __init__(
        self,
        *,
        model_path: Path,
        binary: str = "whisper-cli",
        ffmpeg_binary: str = "ffmpeg",
    ) -> None:
        self.model_path = model_path.expanduser().resolve(strict=False)
        self.binary = binary
        self.ffmpeg_binary = ffmpeg_binary

    def build_command(
        self,
        *,
        audio_path: Path,
        output_base: Path,
        options: TranscriptionOptions,
    ) -> list[str]:
        command = [
            self.binary,
            "-m",
            str(self.model_path),
            "-l",
            options.language,
            "-p",
            "1",
            "-ojf",
            "-of",
            str(output_base),
            "-np",
            "-sns",
        ]
        if options.prompt:
            command.extend(["--prompt", options.prompt])
        command.extend(["-f", str(audio_path)])
        return command

    def transcribe(self, media: MediaItem, options: TranscriptionOptions) -> Transcript:
        if not self.model_path.is_file():
            raise VideoEditingError(f"whisper.cpp model not found: {self.model_path}")
        with tempfile.TemporaryDirectory(prefix="video-editing-th-") as temporary_directory:
            temporary_root = Path(temporary_directory)
            audio_path = temporary_root / "audio.wav"
            output_base = temporary_root / "transcript"
            extract_command = [
                self.ffmpeg_binary,
                "-y",
                "-i",
                str(media.source_path),
                "-vn",
                "-ac",
                "1",
                "-ar",
                "16000",
                "-c:a",
                "pcm_s16le",
                str(audio_path),
            ]
            self._run(extract_command, "audio extraction")
            self._run(
                self.build_command(
                    audio_path=audio_path,
                    output_base=output_base,
                    options=options,
                ),
                "whisper.cpp transcription",
            )
            output_path = output_base.with_suffix(".json")
            if not output_path.is_file():
                raise VideoEditingError("whisper.cpp did not create the expected JSON output")
            payload = json.loads(output_path.read_text(encoding="utf-8"))
        return self.parse_payload(
            payload,
            media_sha256=media.sha256,
            source_path=media.source_path,
            model=self.model_path.stem,
        )

    @staticmethod
    def _run(command: list[str], operation: str) -> None:
        try:
            subprocess.run(command, check=True, capture_output=True, text=True)
        except (OSError, subprocess.CalledProcessError) as exc:
            detail = getattr(exc, "stderr", "") or str(exc)
            raise VideoEditingError(f"{operation} failed: {detail.strip()}") from exc

    @staticmethod
    def parse_payload(
        payload: dict[str, Any],
        *,
        media_sha256: str,
        source_path: Path,
        model: str,
    ) -> Transcript:
        result = payload.get("result", {})
        language = result.get("language", "th") if isinstance(result, dict) else "th"
        raw_segments = payload.get("transcription", [])
        if not isinstance(raw_segments, list):
            raise ValueError("whisper.cpp JSON is missing a transcription list")

        words: list[TranscriptWord] = []
        segments: list[TranscriptSegment] = []
        for segment_index, raw_segment in enumerate(raw_segments):
            if not isinstance(raw_segment, dict):
                continue
            start, end = _offset_seconds(raw_segment.get("offsets"))
            text = str(raw_segment.get("text", "")).strip()
            word_indices: list[int] = []
            raw_tokens = raw_segment.get("tokens", [])
            if isinstance(raw_tokens, list):
                for token in raw_tokens:
                    if not isinstance(token, dict):
                        continue
                    token_text = str(token.get("text", "")).strip()
                    token_start, token_end = _offset_seconds(token.get("offsets"))
                    if not token_text or token_end <= token_start:
                        continue
                    word_indices.append(len(words))
                    words.append(
                        TranscriptWord(
                            text=token_text,
                            start=token_start,
                            end=token_end,
                            probability=_bounded_probability(token.get("p")),
                        )
                    )
            if not word_indices and text and end > start:
                word_indices.append(len(words))
                words.append(TranscriptWord(text=text, start=start, end=end))
            if end <= start:
                continue
            probabilities = [
                words[index].probability
                for index in word_indices
                if words[index].probability is not None
            ]
            confidence = sum(probabilities) / len(probabilities) if probabilities else None
            segments.append(
                TranscriptSegment(
                    id=f"s{segment_index}",
                    start=start,
                    end=end,
                    text=text,
                    word_indices=word_indices,
                    confidence=confidence,
                )
            )

        return Transcript(
            media_sha256=media_sha256,
            source_path=source_path,
            language=str(language).lower(),
            backend="whisper.cpp",
            model=model,
            words=words,
            segments=segments,
        )


def _offset_seconds(value: Any) -> tuple[float, float]:
    if not isinstance(value, dict):
        return 0.0, 0.0
    try:
        return float(value.get("from", 0)) / 1000.0, float(value.get("to", 0)) / 1000.0
    except (TypeError, ValueError):
        return 0.0, 0.0


def _bounded_probability(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return max(0.0, min(1.0, float(value)))
    except (TypeError, ValueError):
        return None
