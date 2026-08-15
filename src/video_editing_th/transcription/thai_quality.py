"""Thai Unicode normalization and transcript hallucination detection."""

from __future__ import annotations

import re
import unicodedata
from collections import Counter

from ..models import (
    IssueSeverity,
    QualityIssue,
    QualityReport,
    Transcript,
    TranscriptSegment,
)

THAI_START = 0x0E00
THAI_END = 0x0E7F
CJK_RANGES = (
    (0x3400, 0x4DBF),
    (0x4E00, 0x9FFF),
    (0xF900, 0xFAFF),
)


def normalize_thai_transcript(transcript: Transcript) -> Transcript:
    """Return a canonical NFC-normalized transcript without mutating the input."""

    normalized_words = [
        word.model_copy(update={"text": unicodedata.normalize("NFC", word.text)})
        for word in transcript.words
    ]
    normalized_segments = [
        segment.model_copy(update={"text": unicodedata.normalize("NFC", segment.text)})
        for segment in transcript.segments
    ]
    return transcript.model_copy(
        update={"words": normalized_words, "segments": normalized_segments}
    )


def validate_thai_transcript(transcript: Transcript) -> QualityReport:
    """Reject the multilingual and repetition failure modes seen in corrupted Thai ASR."""

    transcript = normalize_thai_transcript(transcript)
    text = " ".join(segment.text for segment in transcript.segments if segment.text.strip())
    thai_count = sum(_is_thai(character) for character in text)
    cjk_count = sum(_is_cjk(character) for character in text)
    latin_count = sum(_is_latin(character) for character in text)
    other_letter_count = sum(
        unicodedata.category(character).startswith(("L", "M"))
        and not _is_thai(character)
        and not _is_cjk(character)
        and not _is_latin(character)
        for character in text
    )
    script_count = thai_count + cjk_count + latin_count + other_letter_count
    thai_ratio = thai_count / script_count if script_count else 0.0
    latin_ratio = latin_count / script_count if script_count else 0.0

    issues: list[QualityIssue] = []
    if transcript.language != "th":
        issues.append(
            QualityIssue(
                code="wrong_language",
                severity=IssueSeverity.ERROR,
                message=f"Transcript language is {transcript.language!r}, expected 'th'.",
            )
        )
    if not text.strip():
        issues.append(
            QualityIssue(
                code="empty_transcript",
                severity=IssueSeverity.ERROR,
                message="Transcript contains no speech text.",
            )
        )
    if cjk_count:
        issues.append(
            QualityIssue(
                code="unexpected_cjk",
                severity=IssueSeverity.ERROR,
                message=f"Detected {cjk_count} unexpected CJK characters in Thai transcription.",
                segment_ids=[
                    segment.id
                    for segment in transcript.segments
                    if any(_is_cjk(character) for character in segment.text)
                ],
            )
        )
    if script_count >= 5 and thai_ratio < 0.55:
        issues.append(
            QualityIssue(
                code="low_thai_ratio",
                severity=IssueSeverity.ERROR,
                message=f"Only {thai_ratio:.1%} of script characters are Thai.",
            )
        )

    latin_heavy_segments = [
        segment.id for segment in transcript.segments if _segment_is_latin_heavy(segment)
    ]
    if latin_heavy_segments:
        issues.append(
            QualityIssue(
                code="latin_heavy_segments",
                severity=IssueSeverity.WARNING,
                message="Segments are dominated by Latin text; verify intended English terms.",
                segment_ids=latin_heavy_segments,
            )
        )

    normalized_phrases = [_phrase_key(segment.text) for segment in transcript.segments]
    phrase_counts = Counter(phrase for phrase in normalized_phrases if len(phrase) >= 4)
    repeated = [phrase for phrase, count in phrase_counts.items() if count >= 4]
    if repeated:
        affected = [
            segment.id
            for segment, phrase in zip(transcript.segments, normalized_phrases, strict=True)
            if phrase in repeated
        ]
        issues.append(
            QualityIssue(
                code="repeated_phrase",
                severity=IssueSeverity.ERROR,
                message="Detected an implausibly repeated phrase pattern.",
                segment_ids=affected,
            )
        )

    non_speech_segments = [
        segment.id
        for segment in transcript.segments
        if (segment.no_speech_probability or 0) >= 0.8 and len(segment.text.strip()) >= 4
    ]
    if non_speech_segments:
        issues.append(
            QualityIssue(
                code="speech_during_non_speech",
                severity=IssueSeverity.WARNING,
                message="ASR emitted text in regions marked as probable non-speech.",
                segment_ids=non_speech_segments,
            )
        )

    error_count = sum(issue.severity == IssueSeverity.ERROR for issue in issues)
    warning_count = sum(issue.severity == IssueSeverity.WARNING for issue in issues)
    score = max(0.0, 1.0 - min(0.9, error_count * 0.45 + warning_count * 0.1))
    safe = error_count == 0 and thai_ratio >= 0.55 and bool(text.strip())
    return QualityReport(
        safe_for_automatic_editing=safe,
        score=score,
        issues=issues,
        metrics={
            "thai_character_ratio": thai_ratio,
            "latin_character_ratio": latin_ratio,
            "thai_character_count": float(thai_count),
            "cjk_character_count": float(cjk_count),
            "segment_count": float(len(transcript.segments)),
        },
    )


def _is_thai(character: str) -> bool:
    return THAI_START <= ord(character) <= THAI_END


def _is_cjk(character: str) -> bool:
    codepoint = ord(character)
    return any(start <= codepoint <= end for start, end in CJK_RANGES)


def _is_latin(character: str) -> bool:
    if not character.isalpha():
        return False
    return "LATIN" in unicodedata.name(character, "")


def _segment_is_latin_heavy(segment: TranscriptSegment) -> bool:
    letters = [character for character in segment.text if character.isalpha()]
    if len(letters) < 6:
        return False
    latin = sum(_is_latin(character) for character in letters)
    thai = sum(_is_thai(character) for character in letters)
    return latin / len(letters) >= 0.7 and thai / len(letters) < 0.2


def _phrase_key(text: str) -> str:
    return re.sub(r"[^\w\u0E00-\u0E7F]+", "", text.casefold(), flags=re.UNICODE)
