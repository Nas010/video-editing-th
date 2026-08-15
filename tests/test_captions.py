from pathlib import Path

from video_editing_th.captions import build_caption_cues, build_srt
from video_editing_th.config import EditingProfile
from video_editing_th.models import (
    ClipDecision,
    EditPlan,
    Transcript,
    TranscriptSegment,
    TranscriptWord,
)


def test_captions_map_source_words_to_output_timeline_and_chunk_thai(tmp_path: Path) -> None:
    source = tmp_path / "source.mov"
    transcript = Transcript(
        media_sha256="a" * 64,
        source_path=source,
        language="th",
        backend="test",
        model="test",
        words=[
            TranscriptWord(text="สวัสดี", start=10.0, end=10.4),
            TranscriptWord(text="ครับ", start=10.42, end=10.8),
            TranscriptWord(text="วันนี้", start=10.9, end=11.3),
        ],
        segments=[
            TranscriptSegment(
                id="s0", start=10, end=11.3, text="สวัสดีครับวันนี้", word_indices=[0, 1, 2]
            )
        ],
    )
    plan = EditPlan(
        project_id="p1",
        profile_name="test",
        structural_clips=[
            ClipDecision(
                id="c1",
                source_path=source,
                source_sha256="a" * 64,
                source_start=9.9,
                source_end=11.4,
                timeline_start=2.0,
                timeline_end=3.5,
                reason="keep",
                confidence=1,
            )
        ],
    )
    profile = EditingProfile.model_validate(
        {
            "name": "test",
            "version": 1,
            "language": "th",
            "captions": {"enabled": True, "max_characters_per_card": 10, "max_lines": 2},
        }
    )

    cues = build_caption_cues(plan, {"a" * 64: transcript}, profile)

    assert [cue.text for cue in cues] == ["สวัสดีครับ", "วันนี้"]
    assert cues[0].start == 2.1
    assert cues[0].end == 2.9
    srt = build_srt(cues)
    assert "00:00:02,100 --> 00:00:02,900" in srt
    assert "สวัสดีครับ" in srt
