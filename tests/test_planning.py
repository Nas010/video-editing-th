from pathlib import Path

from video_editing_th.config import EditingProfile
from video_editing_th.models import (
    ClipDecision,
    CreativeOperation,
    CreativeOperationKind,
    EditPlan,
    Transcript,
    TranscriptSegment,
    TranscriptWord,
)
from video_editing_th.planning import validate_edit_plan


def profile() -> EditingProfile:
    return EditingProfile.model_validate({"name": "test", "version": 1, "language": "th"})


def transcript(path: Path) -> Transcript:
    return Transcript(
        media_sha256="a" * 64,
        source_path=path,
        language="th",
        backend="test",
        model="test",
        words=[
            TranscriptWord(text="สวัสดี", start=1.0, end=1.5),
            TranscriptWord(text="ครับ", start=1.55, end=2.0),
        ],
        segments=[
            TranscriptSegment(
                id="s0", start=1.0, end=2.0, text="สวัสดีครับ", word_indices=[0, 1]
            )
        ],
    )


def clip(path: Path, *, source_start: float = 0.9, source_end: float = 2.1) -> ClipDecision:
    return ClipDecision(
        id="c1",
        source_path=path,
        source_sha256="a" * 64,
        source_start=source_start,
        source_end=source_end,
        timeline_start=0.0,
        timeline_end=source_end - source_start,
        reason="latest complete take",
        confidence=0.95,
    )


def test_plan_validation_rejects_cut_inside_spoken_word(tmp_path: Path) -> None:
    source = tmp_path / "source.mov"
    plan = EditPlan(
        project_id="p1",
        profile_name="test",
        structural_clips=[clip(source, source_start=1.2, source_end=2.1)],
    )

    result = validate_edit_plan(plan, {"a" * 64: transcript(source)}, profile())

    assert result.valid is False
    assert any("inside spoken word" in error for error in result.errors)


def test_plan_validation_rejects_sfx_above_profile_gain_limit(tmp_path: Path) -> None:
    source = tmp_path / "source.mov"
    plan = EditPlan(
        project_id="p1",
        profile_name="test",
        structural_clips=[clip(source)],
        creative_operations=[
            CreativeOperation(
                id="sfx1",
                kind=CreativeOperationKind.SFX,
                timeline_start=0.5,
                asset_path=tmp_path / "pop.wav",
                parameters={"gain_db": -2},
                reason="accent graphic",
                confidence=0.9,
            )
        ],
    )

    result = validate_edit_plan(plan, {"a" * 64: transcript(source)}, profile())

    assert result.valid is False
    assert any("gain" in error for error in result.errors)


def test_valid_plan_passes_with_review_warning(tmp_path: Path) -> None:
    source = tmp_path / "source.mov"
    review_clip = clip(source).model_copy(update={"review_required": True})
    plan = EditPlan(
        project_id="p1",
        profile_name="test",
        structural_clips=[review_clip],
    )

    result = validate_edit_plan(plan, {"a" * 64: transcript(source)}, profile())

    assert result.valid is True
    assert any("review" in warning for warning in result.warnings)


def test_plan_validation_rejects_transcript_that_fails_thai_quality_gate(
    tmp_path: Path,
) -> None:
    source = tmp_path / "source.mov"
    corrupted = Transcript(
        media_sha256="a" * 64,
        source_path=source,
        language="th",
        backend="test",
        model="test",
        words=[TranscriptWord(text="你好你好", start=1.0, end=2.0)],
        segments=[
            TranscriptSegment(
                id="s0",
                start=1.0,
                end=2.0,
                text="你好你好",
                word_indices=[0],
            )
        ],
    )
    plan = EditPlan(
        project_id="p1",
        profile_name="test",
        structural_clips=[clip(source)],
    )

    result = validate_edit_plan(plan, {"a" * 64: corrupted}, profile())

    assert result.valid is False
    assert any("Thai quality gate" in error for error in result.errors)
