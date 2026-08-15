"""Compact transcript representation for Codex editorial reasoning."""

from __future__ import annotations

from dataclasses import dataclass

from .models import Transcript, TranscriptWord


@dataclass(frozen=True, slots=True)
class PackedPhrase:
    start: float
    end: float
    text: str
    speaker: str | None
    word_indices: tuple[int, ...]


def pack_transcript(transcript: Transcript, *, break_seconds: float = 0.5) -> list[PackedPhrase]:
    if break_seconds < 0:
        raise ValueError("break_seconds must be non-negative")
    if not transcript.words:
        return [
            PackedPhrase(
                start=segment.start,
                end=segment.end,
                text=segment.text.strip(),
                speaker=segment.speaker,
                word_indices=tuple(segment.word_indices),
            )
            for segment in transcript.segments
            if segment.text.strip()
        ]

    phrases: list[PackedPhrase] = []
    current_indices: list[int] = []
    current_words: list[TranscriptWord] = []
    current_speaker: str | None = None

    def flush() -> None:
        nonlocal current_indices, current_words, current_speaker
        if not current_words:
            return
        phrases.append(
            PackedPhrase(
                start=current_words[0].start,
                end=current_words[-1].end,
                text=_join_tokens([word.text for word in current_words]),
                speaker=current_speaker,
                word_indices=tuple(current_indices),
            )
        )
        current_indices = []
        current_words = []
        current_speaker = None

    previous_end: float | None = None
    for index, word in enumerate(transcript.words):
        gap = word.start - previous_end if previous_end is not None else 0.0
        speaker_changed = (
            current_speaker is not None
            and word.speaker is not None
            and word.speaker != current_speaker
        )
        if current_words and (gap >= break_seconds or speaker_changed):
            flush()
        if not current_words:
            current_speaker = word.speaker
        current_indices.append(index)
        current_words.append(word)
        previous_end = word.end
    flush()
    return phrases


def render_packed_markdown(source_name: str, phrases: list[PackedPhrase]) -> str:
    lines = [f"## {source_name}  ({len(phrases)} phrases)", ""]
    for phrase in phrases:
        speaker = f" {phrase.speaker}" if phrase.speaker else ""
        lines.append(f"  [{phrase.start:06.2f}-{phrase.end:06.2f}]{speaker} {phrase.text}")
    lines.append("")
    return "\n".join(lines)


def _join_tokens(tokens: list[str]) -> str:
    output = ""
    for raw_token in tokens:
        token = raw_token.strip()
        if not token:
            continue
        if output and _needs_ascii_space(output[-1], token[0]):
            output += " "
        output += token
    return output


def _needs_ascii_space(previous: str, current: str) -> bool:
    return previous.isascii() and current.isascii() and previous.isalnum() and current.isalnum()
