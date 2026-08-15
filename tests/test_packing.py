from video_editing_th.models import Transcript, TranscriptSegment, TranscriptWord
from video_editing_th.packing import pack_transcript, render_packed_markdown


def test_pack_transcript_breaks_on_gap_and_keeps_thai_unspaced() -> None:
    words = [
        TranscriptWord(text="สวัสดี", start=0.0, end=0.4, speaker="S0"),
        TranscriptWord(text="ครับ", start=0.42, end=0.8, speaker="S0"),
        TranscriptWord(text="วันนี้", start=1.6, end=2.0, speaker="S0"),
        TranscriptWord(text="hello", start=2.05, end=2.3, speaker="S0"),
        TranscriptWord(text="world", start=2.32, end=2.7, speaker="S0"),
    ]
    transcript = Transcript(
        media_sha256="a" * 64,
        language="th",
        backend="test",
        model="test",
        words=words,
        segments=[
            TranscriptSegment(id="s0", start=0.0, end=2.7, text="", word_indices=list(range(5)))
        ],
    )

    phrases = pack_transcript(transcript, break_seconds=0.5)

    assert [phrase.text for phrase in phrases] == ["สวัสดีครับ", "วันนี้hello world"]
    markdown = render_packed_markdown("take-01", phrases)
    assert "## take-01" in markdown
    assert "[000.00-000.80] S0 สวัสดีครับ" in markdown
