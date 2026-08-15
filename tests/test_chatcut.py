from pathlib import Path

from video_editing_th.chatcut import build_chatcut_execution_manifest
from video_editing_th.models import (
    CaptionCue,
    ClipDecision,
    CreativeOperation,
    CreativeOperationKind,
    EditPlan,
)


def test_chatcut_manifest_orders_structural_caption_visual_motion_and_audio(tmp_path: Path) -> None:
    plan = EditPlan(
        project_id="p1",
        profile_name="test",
        structural_clips=[
            ClipDecision(
                id="clip",
                source_path=tmp_path / "source.mov",
                source_sha256="a" * 64,
                source_start=1,
                source_end=3,
                timeline_start=0,
                timeline_end=2,
                reason="keep",
                confidence=1,
            )
        ],
        captions=[CaptionCue(id="cap", start=0.1, end=1.8, text="สวัสดี")],
        creative_operations=[
            CreativeOperation(
                id="sfx",
                kind=CreativeOperationKind.SFX,
                timeline_start=0.5,
                asset_path=tmp_path / "pop.wav",
                parameters={"gain_db": -12},
                reason="accent",
                confidence=1,
            ),
            CreativeOperation(
                id="zoom",
                kind=CreativeOperationKind.PUNCH_IN,
                timeline_start=0.2,
                timeline_end=1.0,
                parameters={"scale": 1.12},
                reason="emphasis",
                confidence=1,
            ),
            CreativeOperation(
                id="broll",
                kind=CreativeOperationKind.BROLL,
                timeline_start=0.4,
                timeline_end=1.4,
                asset_path=tmp_path / "gym.mp4",
                parameters={"source_start": 1.0, "source_end": 2.0},
                reason="illustrate exercise",
                confidence=1,
            ),
        ],
    )

    manifest = build_chatcut_execution_manifest(plan)
    phases = [operation.phase for operation in manifest.operations]

    assert phases == sorted(phases, key=manifest.phase_order.index)
    structural_actions = [
        operation.action for operation in manifest.operations if operation.phase == "structure"
    ]
    assert structural_actions == [
        "place_source_clip"
    ]
    assert any(operation.action == "add_caption" for operation in manifest.operations)
    assert any(operation.action == "place_broll" for operation in manifest.operations)
    assert any(operation.action == "add_motion_effect" for operation in manifest.operations)
    assert any(operation.action == "place_sfx" for operation in manifest.operations)
