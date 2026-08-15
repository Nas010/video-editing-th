from pathlib import Path

import pytest
from pydantic import ValidationError

from video_editing_th.models import (
    AssetRecord,
    AssetRole,
    CaptionCue,
    ClipDecision,
    EditPlan,
    MediaItem,
    TranscriptWord,
)


def media_item(tmp_path: Path) -> MediaItem:
    return MediaItem(
        source_path=tmp_path / "source.mov",
        sha256="a" * 64,
        size_bytes=100,
        duration_seconds=10.0,
        width=1080,
        height=1920,
        fps=30.0,
        has_video=True,
        has_audio=True,
    )


def test_models_reject_unknown_schema_version(tmp_path: Path) -> None:
    payload = media_item(tmp_path).model_dump(mode="json")
    payload["schema_version"] = 2

    with pytest.raises(ValidationError, match="schema_version"):
        MediaItem.model_validate(payload)


def test_transcript_word_rejects_reverse_timing() -> None:
    with pytest.raises(ValidationError, match="end must be greater"):
        TranscriptWord(text="สวัสดี", start=2.0, end=1.0)


def test_edit_plan_rejects_overlapping_structural_clips(tmp_path: Path) -> None:
    plan = {
        "project_id": "p1",
        "profile_name": "thai-fast-reel",
        "structural_clips": [
            {
                "id": "c1",
                "source_path": str(tmp_path / "a.mov"),
                "source_sha256": "a" * 64,
                "source_start": 0.0,
                "source_end": 2.0,
                "timeline_start": 0.0,
                "timeline_end": 2.0,
                "reason": "keep",
                "confidence": 0.9,
            },
            {
                "id": "c2",
                "source_path": str(tmp_path / "a.mov"),
                "source_sha256": "a" * 64,
                "source_start": 3.0,
                "source_end": 5.0,
                "timeline_start": 1.5,
                "timeline_end": 3.5,
                "reason": "keep",
                "confidence": 0.9,
            },
        ],
    }

    with pytest.raises(ValidationError, match="overlap"):
        EditPlan.model_validate(plan)


def test_asset_record_derives_orientation(tmp_path: Path) -> None:
    asset = AssetRecord(
        id="asset-1",
        path=tmp_path / "broll.mp4",
        role=AssetRole.BROLL,
        sha256="b" * 64,
        size_bytes=200,
        duration_seconds=4.0,
        width=1080,
        height=1920,
        description="A runner on a treadmill",
    )

    assert asset.orientation == "portrait"


def test_edit_plan_round_trip_contains_captions(tmp_path: Path) -> None:
    clip = ClipDecision(
        id="clip-1",
        source_path=tmp_path / "source.mov",
        source_sha256="c" * 64,
        source_start=1.0,
        source_end=3.0,
        timeline_start=0.0,
        timeline_end=2.0,
        reason="latest complete retake",
        confidence=0.95,
    )
    plan = EditPlan(
        project_id="project-1",
        profile_name="thai-fast-reel",
        structural_clips=[clip],
        captions=[CaptionCue(id="cap-1", start=0.1, end=1.8, text="สวัสดีครับ")],
    )

    restored = EditPlan.model_validate_json(plan.model_dump_json())

    assert restored.structural_clips[0].source_path == tmp_path / "source.mov"
    assert restored.captions[0].text == "สวัสดีครับ"


def test_retake_analysis_is_versioned() -> None:
    from video_editing_th.models import RetakeAnalysis

    analysis = RetakeAnalysis(media_sha256="a" * 64, profile_name="thai", groups=[])

    assert analysis.schema_version == 1
    assert analysis.media_sha256 == "a" * 64
