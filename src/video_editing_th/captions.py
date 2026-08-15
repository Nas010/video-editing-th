"""Thai-aware caption mapping and SRT generation."""

from __future__ import annotations

from dataclasses import dataclass

from .config import EditingProfile
from .models import CaptionCue, EditPlan, Transcript


@dataclass(frozen=True, slots=True)
class _MappedWord:
    text: str
    start: float
    end: float
    source_segment_ids: tuple[str, ...]


def build_caption_cues(
    plan: EditPlan,
    transcripts: dict[str, Transcript],
    profile: EditingProfile,
    *,
    pause_break_seconds: float = 0.35,
) -> list[CaptionCue]:
    if not profile.captions.enabled:
        return []
    mapped: list[_MappedWord] = []
    for clip in sorted(plan.structural_clips, key=lambda item: item.timeline_start):
        transcript = transcripts.get(clip.source_sha256)
        if transcript is None:
            continue
        segment_lookup = _word_segment_lookup(transcript)
        for index, word in enumerate(transcript.words):
            if word.start < clip.source_start - 1e-6 or word.end > clip.source_end + 1e-6:
                continue
            mapped.append(
                _MappedWord(
                    text=word.text.strip(),
                    start=round(clip.timeline_start + word.start - clip.source_start, 3),
                    end=round(clip.timeline_start + word.end - clip.source_start, 3),
                    source_segment_ids=segment_lookup.get(index, ()),
                )
            )

    cues: list[CaptionCue] = []
    current: list[_MappedWord] = []

    def flush() -> None:
        if not current:
            return
        text = _join_tokens([word.text for word in current])
        segment_ids = tuple(
            dict.fromkeys(segment_id for word in current for segment_id in word.source_segment_ids)
        )
        cues.append(
            CaptionCue(
                id=f"cap-{len(cues) + 1:04d}",
                start=current[0].start,
                end=max(current[-1].end, current[0].start + 0.05),
                text=text,
                source_segment_ids=list(segment_ids),
            )
        )
        current.clear()

    for word in mapped:
        if not word.text:
            continue
        proposed = _join_tokens([item.text for item in current] + [word.text])
        gap = word.start - current[-1].end if current else 0.0
        if current and (
            len(proposed) > profile.captions.max_characters_per_card or gap >= pause_break_seconds
        ):
            flush()
        current.append(word)
    flush()
    return cues


def build_srt(cues: list[CaptionCue]) -> str:
    blocks: list[str] = []
    for index, cue in enumerate(cues, start=1):
        blocks.append(
            f"{index}\n{_srt_timestamp(cue.start)} --> {_srt_timestamp(cue.end)}\n{cue.text}"
        )
    return "\n\n".join(blocks) + ("\n" if blocks else "")


def _word_segment_lookup(transcript: Transcript) -> dict[int, tuple[str, ...]]:
    lookup: dict[int, list[str]] = {}
    for segment in transcript.segments:
        for index in segment.word_indices:
            lookup.setdefault(index, []).append(segment.id)
    return {index: tuple(values) for index, values in lookup.items()}


def _join_tokens(tokens: list[str]) -> str:
    output = ""
    for raw in tokens:
        token = raw.strip()
        if not token:
            continue
        if (
            output
            and output[-1].isascii()
            and token[0].isascii()
            and output[-1].isalnum()
            and token[0].isalnum()
        ):
            output += " "
        output += token
    return output


def _srt_timestamp(seconds: float) -> str:
    milliseconds = max(0, round(seconds * 1000))
    hours, remainder = divmod(milliseconds, 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    secs, millis = divmod(remainder, 1_000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"
