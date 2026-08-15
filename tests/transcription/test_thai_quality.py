import unicodedata

from video_editing_th.models import Transcript, TranscriptSegment, TranscriptWord
from video_editing_th.transcription.thai_quality import (
    normalize_thai_transcript,
    validate_thai_transcript,
)


def make_transcript(texts: list[str], *, language: str = "th") -> Transcript:
    words = []
    segments = []
    for index, text in enumerate(texts):
        start = float(index * 2)
        end = start + 1.5
        words.append(TranscriptWord(text=text, start=start, end=end, probability=0.9))
        segments.append(
            TranscriptSegment(
                id=f"s{index}",
                start=start,
                end=end,
                text=text,
                word_indices=[index],
                confidence=0.9,
            )
        )
    return Transcript(
        media_sha256="a" * 64,
        language=language,
        backend="test",
        model="test",
        words=words,
        segments=segments,
    )


def test_good_thai_transcript_is_safe() -> None:
    report = validate_thai_transcript(
        make_transcript(["สวัสดีครับวันนี้เราจะมาพูดเรื่องการออกกำลังกาย", "เริ่มกันเลยครับ"])
    )

    assert report.safe_for_automatic_editing is True
    assert report.score >= 0.8
    assert report.metrics["thai_character_ratio"] > 0.8


def test_cjk_hallucination_is_rejected() -> None:
    report = validate_thai_transcript(make_transcript(["人哋叫佢去攞樽", "สวัสดีครับ"]))

    assert report.safe_for_automatic_editing is False
    assert any(issue.code == "unexpected_cjk" for issue in report.issues)


def test_repeated_latin_hallucination_is_rejected() -> None:
    report = validate_thai_transcript(make_transcript(["I'm so tired"] * 8))

    assert report.safe_for_automatic_editing is False
    codes = {issue.code for issue in report.issues}
    assert "low_thai_ratio" in codes
    assert "repeated_phrase" in codes


def test_normalization_returns_nfc_thai_text() -> None:
    decomposed = unicodedata.normalize("NFD", "กำลัง")
    normalized = normalize_thai_transcript(make_transcript([decomposed]))

    assert normalized.segments[0].text == unicodedata.normalize("NFC", decomposed)
    assert normalized.words[0].text == unicodedata.normalize("NFC", decomposed)
