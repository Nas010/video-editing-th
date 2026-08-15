"""Canonical, versioned data contracts for the editing pipeline."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from itertools import pairwise
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

SCHEMA_VERSION: Literal[1] = 1
Sha256 = str


class CanonicalModel(BaseModel):
    """Strict immutable base model used for persisted pipeline artifacts."""

    model_config = ConfigDict(extra="forbid", frozen=True)
    schema_version: Literal[1] = SCHEMA_VERSION


class TimedModel(CanonicalModel):
    start: float = Field(ge=0)
    end: float = Field(gt=0)

    @model_validator(mode="after")
    def validate_timing(self) -> TimedModel:
        if self.end <= self.start:
            raise ValueError("end must be greater than start")
        return self


class MediaItem(CanonicalModel):
    source_path: Path
    sha256: Sha256 = Field(pattern=r"^[0-9a-f]{64}$")
    size_bytes: int = Field(ge=0)
    duration_seconds: float = Field(ge=0)
    width: int | None = Field(default=None, ge=1)
    height: int | None = Field(default=None, ge=1)
    fps: float | None = Field(default=None, gt=0)
    has_video: bool = True
    has_audio: bool = True
    video_codec: str | None = None
    audio_codec: str | None = None
    created_at_source: datetime | None = None


class TranscriptWordKind(StrEnum):
    WORD = "word"
    AUDIO_EVENT = "audio_event"


class TranscriptWord(TimedModel):
    text: str = Field(min_length=1)
    probability: float | None = Field(default=None, ge=0, le=1)
    speaker: str | None = None
    kind: TranscriptWordKind = TranscriptWordKind.WORD


class TranscriptSegment(TimedModel):
    id: str = Field(min_length=1)
    text: str = ""
    word_indices: list[int] = Field(default_factory=list)
    confidence: float | None = Field(default=None, ge=0, le=1)
    no_speech_probability: float | None = Field(default=None, ge=0, le=1)
    speaker: str | None = None

    @field_validator("word_indices")
    @classmethod
    def indices_must_be_non_negative(cls, value: list[int]) -> list[int]:
        if any(index < 0 for index in value):
            raise ValueError("word indices must be non-negative")
        return value


class Transcript(CanonicalModel):
    media_sha256: Sha256 = Field(pattern=r"^[0-9a-f]{64}$")
    language: str = Field(default="th", pattern=r"^[a-z]{2,3}$")
    backend: str = Field(min_length=1)
    model: str = Field(min_length=1)
    words: list[TranscriptWord] = Field(default_factory=list)
    segments: list[TranscriptSegment] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    source_path: Path | None = None

    @model_validator(mode="after")
    def validate_order_and_indices(self) -> Transcript:
        previous_start = -1.0
        for word in self.words:
            if word.start < previous_start:
                raise ValueError("transcript words must be sorted by start time")
            previous_start = word.start
        previous_start = -1.0
        for segment in self.segments:
            if segment.start < previous_start:
                raise ValueError("transcript segments must be sorted by start time")
            if any(index >= len(self.words) for index in segment.word_indices):
                raise ValueError("segment references a word index outside the transcript")
            previous_start = segment.start
        return self


class IssueSeverity(StrEnum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


class QualityIssue(CanonicalModel):
    code: str = Field(min_length=1)
    severity: IssueSeverity
    message: str = Field(min_length=1)
    segment_ids: list[str] = Field(default_factory=list)


class QualityReport(CanonicalModel):
    safe_for_automatic_editing: bool
    score: float = Field(ge=0, le=1)
    issues: list[QualityIssue] = Field(default_factory=list)
    metrics: dict[str, float] = Field(default_factory=dict)


class SilenceInterval(TimedModel):
    duration: float = Field(gt=0)

    @model_validator(mode="after")
    def duration_matches_bounds(self) -> SilenceInterval:
        if abs(self.duration - (self.end - self.start)) > 0.02:
            raise ValueError("silence duration must match start/end bounds")
        return self


class RetakeCandidate(CanonicalModel):
    id: str = Field(min_length=1)
    segment_ids: list[str] = Field(min_length=1)
    start: float = Field(ge=0)
    end: float = Field(gt=0)
    text: str = ""
    completeness_score: float = Field(default=0.5, ge=0, le=1)
    restart_score: float = Field(default=0, ge=0, le=1)
    features: dict[str, float | str | bool] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_bounds(self) -> RetakeCandidate:
        if self.end <= self.start:
            raise ValueError("retake candidate end must be greater than start")
        return self


class RetakeGroup(CanonicalModel):
    id: str = Field(min_length=1)
    candidates: list[RetakeCandidate] = Field(min_length=2)
    recommended_candidate_id: str | None = None
    confidence: float = Field(default=0, ge=0, le=1)
    requires_review: bool = True

    @model_validator(mode="after")
    def recommended_candidate_exists(self) -> RetakeGroup:
        if self.recommended_candidate_id is not None and self.recommended_candidate_id not in {
            candidate.id for candidate in self.candidates
        }:
            raise ValueError("recommended candidate must belong to the retake group")
        return self


class RetakeAnalysis(CanonicalModel):
    media_sha256: Sha256 = Field(pattern=r"^[0-9a-f]{64}$")
    profile_name: str = Field(min_length=1)
    groups: list[RetakeGroup] = Field(default_factory=list)


class AssetRole(StrEnum):
    BROLL = "broll"
    OVERLAY = "overlay"
    SFX = "sfx"
    MUSIC = "music"
    TRANSITION = "transition"
    BACKGROUND = "background"
    IMAGE = "image"


class AssetRecord(CanonicalModel):
    id: str = Field(min_length=1)
    path: Path
    role: AssetRole
    sha256: Sha256 = Field(pattern=r"^[0-9a-f]{64}$")
    size_bytes: int = Field(ge=0)
    duration_seconds: float | None = Field(default=None, ge=0)
    width: int | None = Field(default=None, ge=1)
    height: int | None = Field(default=None, ge=1)
    fps: float | None = Field(default=None, gt=0)
    has_audio: bool = False
    transparent: bool = False
    orientation: Literal["portrait", "landscape", "square", "audio", "unknown"] = "unknown"
    description: str = ""
    tags: list[str] = Field(default_factory=list)
    use_cases: list[str] = Field(default_factory=list)
    shot_type: str | None = None
    camera_motion: str | None = None
    contact_sheet_path: Path | None = None
    indexed_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @model_validator(mode="after")
    def derive_orientation(self) -> AssetRecord:
        orientation = self.orientation
        if orientation == "unknown":
            if self.width is None or self.height is None:
                orientation = "audio" if self.duration_seconds is not None else "unknown"
            elif self.width == self.height:
                orientation = "square"
            elif self.width > self.height:
                orientation = "landscape"
            else:
                orientation = "portrait"
            object.__setattr__(self, "orientation", orientation)
        return self


class ClipDecision(CanonicalModel):
    id: str = Field(min_length=1)
    source_path: Path
    source_sha256: Sha256 = Field(pattern=r"^[0-9a-f]{64}$")
    source_start: float = Field(ge=0)
    source_end: float = Field(gt=0)
    timeline_start: float = Field(ge=0)
    timeline_end: float = Field(gt=0)
    reason: str = Field(min_length=1)
    confidence: float = Field(ge=0, le=1)
    retake_group_id: str | None = None
    review_required: bool = False

    @model_validator(mode="after")
    def validate_durations(self) -> ClipDecision:
        if self.source_end <= self.source_start:
            raise ValueError("source_end must be greater than source_start")
        if self.timeline_end <= self.timeline_start:
            raise ValueError("timeline_end must be greater than timeline_start")
        source_duration = self.source_end - self.source_start
        timeline_duration = self.timeline_end - self.timeline_start
        if abs(source_duration - timeline_duration) > 0.05:
            raise ValueError("structural clip source and timeline durations must match")
        return self


class CaptionCue(TimedModel):
    id: str = Field(min_length=1)
    text: str = Field(min_length=1)
    source_segment_ids: list[str] = Field(default_factory=list)


class CreativeOperationKind(StrEnum):
    BROLL = "broll"
    OVERLAY = "overlay"
    SFX = "sfx"
    PUNCH_IN = "punch_in"
    SLOW_ZOOM = "slow_zoom"
    PAN = "pan"
    REFRAME = "reframe"
    TRANSITION = "transition"


class CreativeOperation(CanonicalModel):
    id: str = Field(min_length=1)
    kind: CreativeOperationKind
    timeline_start: float = Field(ge=0)
    timeline_end: float | None = Field(default=None, gt=0)
    asset_id: str | None = None
    asset_path: Path | None = None
    parameters: dict[str, Any] = Field(default_factory=dict)
    reason: str = Field(min_length=1)
    confidence: float = Field(ge=0, le=1)
    review_required: bool = False

    @model_validator(mode="after")
    def validate_operation(self) -> CreativeOperation:
        if self.timeline_end is not None and self.timeline_end <= self.timeline_start:
            raise ValueError("creative operation end must be greater than start")
        asset_kinds = {
            CreativeOperationKind.BROLL,
            CreativeOperationKind.OVERLAY,
            CreativeOperationKind.SFX,
        }
        if self.kind in asset_kinds and self.asset_id is None and self.asset_path is None:
            raise ValueError("asset operation requires asset_id or asset_path")
        return self


class EditPlan(CanonicalModel):
    project_id: str = Field(min_length=1)
    profile_name: str = Field(min_length=1)
    structural_clips: list[ClipDecision] = Field(default_factory=list)
    captions: list[CaptionCue] = Field(default_factory=list)
    creative_operations: list[CreativeOperation] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @model_validator(mode="after")
    def validate_timeline(self) -> EditPlan:
        ordered_clips = sorted(self.structural_clips, key=lambda clip: clip.timeline_start)
        for previous_clip, current_clip in pairwise(ordered_clips):
            if current_clip.timeline_start < previous_clip.timeline_end - 1e-6:
                raise ValueError("structural clips overlap on the output timeline")
        ordered_captions = sorted(self.captions, key=lambda cue: cue.start)
        for previous_caption, current_caption in pairwise(ordered_captions):
            if current_caption.start < previous_caption.start:
                raise ValueError("captions must be ordered")
        return self

    @property
    def duration_seconds(self) -> float:
        return max((clip.timeline_end for clip in self.structural_clips), default=0.0)


class ProjectStatus(StrEnum):
    INITIALIZED = "initialized"
    INVENTORIED = "inventoried"
    TRANSCRIBED = "transcribed"
    ANALYZED = "analyzed"
    PLANNED = "planned"
    RENDERED = "rendered"


class ProjectManifest(CanonicalModel):
    project_id: str = Field(min_length=1)
    root: Path
    edit_dir: Path
    profile_path: Path
    profile_name: str
    status: ProjectStatus = ProjectStatus.INITIALIZED
    media: list[MediaItem] = Field(default_factory=list)
    tool_versions: dict[str, str] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
