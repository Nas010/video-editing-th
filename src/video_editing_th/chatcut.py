"""Stable execution manifest for Codex-controlled ChatCut operations."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from .models import CreativeOperationKind, EditPlan

PHASE_ORDER = ["import", "structure", "captions", "visuals", "motion", "audio", "transitions"]


class ChatCutOperation(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    sequence: int = Field(ge=1)
    phase: str
    action: str
    timeline_start: float | None = Field(default=None, ge=0)
    payload: dict[str, Any]


class ChatCutExecutionManifest(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    schema_version: Literal[1] = 1
    project_id: str
    composition_width: int = 1080
    composition_height: int = 1920
    fps: float = 30.0
    phase_order: list[str] = Field(default_factory=lambda: list(PHASE_ORDER))
    operations: list[ChatCutOperation]


def build_chatcut_execution_manifest(
    plan: EditPlan,
    *,
    composition_width: int = 1080,
    composition_height: int = 1920,
    fps: float = 30.0,
) -> ChatCutExecutionManifest:
    pending: list[tuple[str, float, str, str, dict[str, Any]]] = []
    imported_paths: set[str] = set()

    def add_import(path: str, media_role: str) -> None:
        if path in imported_paths:
            return
        imported_paths.add(path)
        pending.append(("import", 0.0, path, "import_media", {"path": path, "role": media_role}))

    for clip in plan.structural_clips:
        add_import(str(clip.source_path), "source")
    for operation in plan.creative_operations:
        if operation.asset_path is not None:
            add_import(str(operation.asset_path), operation.kind.value)

    for clip in plan.structural_clips:
        pending.append(
            (
                "structure",
                clip.timeline_start,
                clip.id,
                "place_source_clip",
                {
                    "id": clip.id,
                    "source_path": str(clip.source_path),
                    "source_start": clip.source_start,
                    "source_end": clip.source_end,
                    "timeline_start": clip.timeline_start,
                    "timeline_end": clip.timeline_end,
                    "reason": clip.reason,
                    "confidence": clip.confidence,
                },
            )
        )
    for cue in plan.captions:
        pending.append(
            (
                "captions",
                cue.start,
                cue.id,
                "add_caption",
                {"id": cue.id, "start": cue.start, "end": cue.end, "text": cue.text},
            )
        )
    for operation in plan.creative_operations:
        common = {
            "id": operation.id,
            "kind": operation.kind.value,
            "start": operation.timeline_start,
            "end": operation.timeline_end,
            "asset_id": operation.asset_id,
            "asset_path": str(operation.asset_path) if operation.asset_path else None,
            "parameters": operation.parameters,
            "reason": operation.reason,
            "confidence": operation.confidence,
        }
        if operation.kind == CreativeOperationKind.BROLL:
            phase, action = "visuals", "place_broll"
        elif operation.kind == CreativeOperationKind.OVERLAY:
            phase, action = "visuals", "place_overlay"
        elif operation.kind == CreativeOperationKind.SFX:
            phase, action = "audio", "place_sfx"
        elif operation.kind == CreativeOperationKind.MUSIC:
            phase, action = "audio", "place_music"
        elif operation.kind == CreativeOperationKind.TRANSITION:
            phase, action = "transitions", "add_transition"
        else:
            phase, action = "motion", "add_motion_effect"
        pending.append((phase, operation.timeline_start, operation.id, action, common))

    pending.sort(key=lambda item: (PHASE_ORDER.index(item[0]), item[1], item[2]))
    operations = [
        ChatCutOperation(
            sequence=index,
            phase=phase,
            action=action,
            timeline_start=timeline_start,
            payload=payload,
        )
        for index, (phase, timeline_start, _stable_id, action, payload) in enumerate(
            pending, start=1
        )
    ]
    return ChatCutExecutionManifest(
        project_id=plan.project_id,
        composition_width=composition_width,
        composition_height=composition_height,
        fps=fps,
        operations=operations,
    )
