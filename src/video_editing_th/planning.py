"""Cross-cutting validation for canonical edit plans."""

from __future__ import annotations

from dataclasses import dataclass
from math import ceil

from .config import EditingProfile
from .models import CreativeOperationKind, EditPlan, Transcript
from .transcription.thai_quality import validate_thai_transcript


@dataclass(frozen=True, slots=True)
class PlanValidationResult:
    errors: tuple[str, ...]
    warnings: tuple[str, ...]

    @property
    def valid(self) -> bool:
        return not self.errors

    def raise_for_errors(self) -> None:
        if self.errors:
            raise ValueError("Invalid edit plan:\n- " + "\n- ".join(self.errors))


def validate_edit_plan(
    plan: EditPlan,
    transcripts: dict[str, Transcript],
    profile: EditingProfile,
    *,
    edge_tolerance_seconds: float = 0.015,
) -> PlanValidationResult:
    errors: list[str] = []
    warnings: list[str] = list(plan.warnings)

    for source_sha256, transcript in transcripts.items():
        quality = validate_thai_transcript(transcript)
        if not quality.safe_for_automatic_editing:
            codes = ", ".join(issue.code for issue in quality.issues) or "unknown failure"
            errors.append(f"Transcript {source_sha256[:12]} failed the Thai quality gate: {codes}.")

    for clip in plan.structural_clips:
        transcript = transcripts.get(clip.source_sha256)
        if transcript is None:
            errors.append(f"Clip {clip.id} has no transcript for source {clip.source_sha256[:12]}.")
            continue
        for edge_name, edge in (("start", clip.source_start), ("end", clip.source_end)):
            for word in transcript.words:
                if word.start + edge_tolerance_seconds < edge < word.end - edge_tolerance_seconds:
                    errors.append(
                        f"Clip {clip.id} {edge_name}={edge:.3f}s falls inside spoken word "
                        f"{word.text!r} ({word.start:.3f}-{word.end:.3f}s)."
                    )
                    break
        if clip.review_required:
            warnings.append(f"Clip {clip.id} still requires editorial review.")
        if clip.confidence < 0.6:
            warnings.append(f"Clip {clip.id} has low selection confidence ({clip.confidence:.2f}).")

    plan_duration = plan.duration_seconds
    for operation in plan.creative_operations:
        if operation.timeline_start > plan_duration + 0.05:
            errors.append(f"Operation {operation.id} starts after the structural timeline ends.")
        if operation.timeline_end is not None and operation.timeline_end > plan_duration + 0.05:
            errors.append(f"Operation {operation.id} ends after the structural timeline ends.")
        if operation.kind == CreativeOperationKind.SFX:
            raw_gain = operation.parameters.get("gain_db", -12.0)
            try:
                gain = float(raw_gain)
            except (TypeError, ValueError):
                errors.append(f"SFX operation {operation.id} has a non-numeric gain value.")
            else:
                if gain > profile.creative.maximum_sfx_gain_db:
                    errors.append(
                        f"SFX operation {operation.id} gain {gain:g} dB exceeds the profile "
                        f"limit of {profile.creative.maximum_sfx_gain_db:g} dB."
                    )
        if operation.review_required:
            warnings.append(f"Creative operation {operation.id} still requires review.")

    _validate_frequency_limits(plan, profile, errors)
    return PlanValidationResult(errors=tuple(errors), warnings=tuple(dict.fromkeys(warnings)))


def _validate_frequency_limits(
    plan: EditPlan,
    profile: EditingProfile,
    errors: list[str],
) -> None:
    if plan.duration_seconds <= 0:
        return
    minutes = max(plan.duration_seconds / 60.0, 1 / 60.0)
    limits = {
        CreativeOperationKind.PUNCH_IN: profile.creative.maximum_punch_ins_per_minute,
        CreativeOperationKind.BROLL: profile.creative.maximum_broll_per_minute,
        CreativeOperationKind.SFX: profile.creative.maximum_sfx_per_minute,
    }
    for kind, per_minute in limits.items():
        count = sum(operation.kind == kind for operation in plan.creative_operations)
        allowed = ceil(per_minute * minutes)
        if count > allowed:
            errors.append(
                f"Plan contains {count} {kind.value} operations; profile allows {allowed} "
                f"for a {plan.duration_seconds:.1f}s edit."
            )
