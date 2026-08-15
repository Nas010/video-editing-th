"""Canonical models for media, transcripts, decisions, and editor operations."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from itertools import pairwise
from pathlib import Path
from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

SCHEMA_VERSION = 1
Sha256 = Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]


class CanonicalModel(BaseModel):
    """Shared immutable schema settings for persisted artifacts."""

    model_config = ConfigDict(extra="forbid", frozen=True)
    schema_version: Literal[1] = 1


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
    sha256: Sha256
    size_bytes: int = Field(ge=0)
    duration_seconds: float = Field(ge=0)
    width: int | None = Field(default=None, ge=1)
    height: int | None = Field(default=None, ge=1)
    fps: float | None = Field(default=None, gt=0)
    has_video: bool
    has_audio: bool
    codec_video: str | None = None
    codec_audio: str | None = None
    creation_time: datetime | None = None


class TranscriptWord(TimedModel):
    text: str = Field(min_length=1)
    probability: float | None = Field(default=None, ge=0, le=1)
    speaker: str | None = None


class TranscriptSegment(TimedModel):
    id: str = Field(min_length=1)
    text: str = Field(min_length=1)
    words: list[TranscriptWord] = Field(default_factory=list)
    confidence: float | None = Field(default=None, ge=0, le=1)
    no_speech_probability: float | None = Field(default=None, ge=0, le=1)
    speaker: str | None = None

    @model_validator(mode="after")
    def validate_word_bounds(self) -> TranscriptSegment:
        for word in self.words:
            if word.start < self.start - 0.05 or word.end > self.end + 0.05:
                raise ValueError("word timing must remain inside its transcript segment")
        return self


class Transcript(CanonicalModel):
    media_sha256: Sha256
    media_path: Path
    language: str = Field(min_length=2, max_length=12)
    backend: str = Field(min_length=1)
    model: str | None = None
    duration_seconds: float = Field(ge=0)
    segments: list[TranscriptSegment] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_chronology(self) -> Transcript:
        for previous, current in pairwise(self.segments):
            if current.start < previous.start:
                raise ValueError("transcript segments must be chronological")
        return self


class TranscriptIssue(CanonicalModel):
    code: str = Field(min_length=1)
    severity: Literal["warning", "error"]
    message: str = Field(min_length=1)
    segment_id: str | None = None


class TranscriptQualityReport(CanonicalModel):
    media_sha256: Sha256
    language: str
    thai_character_ratio: float = Field(ge=0, le=1)
    cjk_character_count: int = Field(ge=0)
    latin_character_ratio: float = Field(ge=0, le=1)
    repeated_segment_count: int = Field(ge=0)
    suspicious_non_speech_segment_count: int = Field(ge=0)
    issues: list[TranscriptIssue] = Field(default_factory=list)
    safe_for_automatic_editing: bool


class SilenceInterval(TimedModel):
    duration: float = Field(ge=0)

    @model_validator(mode="after")
    def derive_duration(self) -> SilenceInterval:
        object.__setattr__(self, "duration", self.end - self.start)
        return self


class RetakeCandidate(CanonicalModel):
    id: str = Field(min_length=1)
    segment_ids: list[str] = Field(min_length=1)
    start: float = Field(ge=0)
    end: float = Field(gt=0)
    text: str = Field(min_length=1)
    complete: bool
    confidence: float = Field(default=0, ge=0, le=1)
    evidence: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_range(self) -> RetakeCandidate:
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
    media_sha256: Sha256
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
    sha256: Sha256
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
    source_sha256: Sha256
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
    MUSIC = "music"
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
            CreativeOperationKind.MUSIC,
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
