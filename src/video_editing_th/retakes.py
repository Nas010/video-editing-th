"""Conservative retake-candidate discovery for Codex review."""

from __future__ import annotations

import re
from difflib import SequenceMatcher

from .config import EditingProfile
from .models import RetakeCandidate, RetakeGroup, Transcript, TranscriptSegment

RESTART_MARKERS = ("เอ่อ", "อ่า", "อืม", "ขอใหม่", "อีกที", "ไม่ใช่", "เดี๋ยว")
ENDING_PARTICLES = ("ครับ", "ค่ะ", "นะ", "เลย", "กัน", "แล้ว")


def text_similarity(first: str, second: str) -> float:
    """Blend sequence and Thai character n-gram similarity."""

    first_key = _normalize_text(first)
    second_key = _normalize_text(second)
    if not first_key or not second_key:
        return 0.0
    sequence_score = SequenceMatcher(None, first_key, second_key, autojunk=False).ratio()
    first_grams = _ngrams(first_key, 3)
    second_grams = _ngrams(second_key, 3)
    if not first_grams or not second_grams:
        ngram_score = sequence_score
    else:
        ngram_score = len(first_grams & second_grams) / len(first_grams | second_grams)
    containment = min(len(first_key), len(second_key)) / max(len(first_key), len(second_key))
    return max(0.0, min(1.0, 0.55 * sequence_score + 0.3 * ngram_score + 0.15 * containment))


def find_retake_groups(transcript: Transcript, profile: EditingProfile) -> list[RetakeGroup]:
    """Find likely repeated attempts without making destructive edit decisions."""

    active_groups: list[list[TranscriptSegment]] = []
    threshold = profile.retakes.similarity_threshold
    maximum_gap = profile.retakes.maximum_gap_seconds

    for segment in transcript.segments:
        if not segment.text.strip():
            continue
        best_group: list[TranscriptSegment] | None = None
        best_score = 0.0
        for group in active_groups:
            last = group[-1]
            if segment.start - last.end > maximum_gap:
                continue
            score = max(text_similarity(segment.text, candidate.text) for candidate in group)
            if score >= threshold and score > best_score:
                best_group = group
                best_score = score
        if best_group is None:
            active_groups.append([segment])
        else:
            best_group.append(segment)

    repeated_groups = [group for group in active_groups if len(group) >= 2]
    results: list[RetakeGroup] = []
    for group_index, group in enumerate(repeated_groups):
        candidates: list[RetakeCandidate] = []
        similarities: list[float] = []
        for candidate_index, segment in enumerate(group):
            restart_score = _restart_score(segment.text)
            completeness = _completeness_score(segment.text, restart_score)
            similarity_to_previous = (
                text_similarity(group[candidate_index - 1].text, segment.text)
                if candidate_index > 0
                else 1.0
            )
            if candidate_index > 0:
                similarities.append(similarity_to_previous)
            candidates.append(
                RetakeCandidate(
                    id=f"retake-{group_index + 1}-take-{candidate_index + 1}",
                    segment_ids=[segment.id],
                    start=segment.start,
                    end=segment.end,
                    text=segment.text,
                    completeness_score=completeness,
                    restart_score=restart_score,
                    features={"similarity_to_previous": similarity_to_previous},
                )
            )

        eligible = [candidate for candidate in candidates if candidate.completeness_score >= 0.55]
        recommendation = (
            eligible[-1].id if eligible and profile.retakes.prefer_latest_complete else None
        )
        confidence = sum(similarities) / len(similarities) if similarities else 0.0
        results.append(
            RetakeGroup(
                id=f"retake-{group_index + 1}",
                candidates=candidates,
                recommended_candidate_id=recommendation,
                confidence=confidence,
                requires_review=profile.retakes.preserve_uncertain,
            )
        )
    return results


def _normalize_text(text: str) -> str:
    return re.sub(r"[^0-9A-Za-z\u0E00-\u0E7F]+", "", text.casefold())


def _ngrams(text: str, size: int) -> set[str]:
    if len(text) < size:
        return {text} if text else set()
    return {text[index : index + size] for index in range(len(text) - size + 1)}


def _restart_score(text: str) -> float:
    normalized = text.strip().casefold()
    hits = sum(marker in normalized for marker in RESTART_MARKERS)
    ending_hit = any(normalized.endswith(marker) for marker in RESTART_MARKERS)
    return min(1.0, hits * 0.35 + (0.45 if ending_hit else 0.0))


def _completeness_score(text: str, restart_score: float) -> float:
    normalized = text.strip()
    length_score = min(1.0, len(_normalize_text(normalized)) / 20)
    ending_bonus = 0.12 if normalized.endswith(ENDING_PARTICLES) else 0.0
    punctuation_bonus = 0.08 if normalized.endswith((".", "!", "?", "ฯ")) else 0.0
    score = 0.45 + 0.35 * length_score + ending_bonus + punctuation_bonus - 0.55 * restart_score
    return max(0.0, min(1.0, score))
