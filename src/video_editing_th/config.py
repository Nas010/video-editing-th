"""Typed application and editing-profile configuration."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from .errors import ConfigurationError


class StrictModel(BaseModel):
    """Shared strict immutable model configuration."""

    model_config = ConfigDict(extra="forbid", frozen=True, validate_default=True)


class PacingProfile(StrictModel):
    intra_thought_target_ms: int = Field(default=90, ge=0, le=2_000)
    sentence_target_ms: int = Field(default=240, ge=0, le=4_000)
    topic_target_ms: int = Field(default=420, ge=0, le=10_000)
    word_handle_ms: int = Field(default=85, ge=0, le=500)
    maximum_audio_overlap_ms: int = Field(default=25, ge=0, le=100)

    @model_validator(mode="after")
    def validate_pause_targets(self) -> PacingProfile:
        targets = (
            self.intra_thought_target_ms,
            self.sentence_target_ms,
            self.topic_target_ms,
        )
        if targets != tuple(sorted(targets)):
            raise ValueError("pause targets must be monotonic: intra-thought <= sentence <= topic")
        return self


class RetakeProfile(StrictModel):
    maximum_gap_seconds: float = Field(default=15.0, gt=0, le=120)
    similarity_threshold: float = Field(default=0.72, ge=0, le=1)
    prefer_latest_complete: bool = True
    preserve_uncertain: bool = True


class CreativeProfile(StrictModel):
    maximum_punch_ins_per_minute: int = Field(default=5, ge=0, le=60)
    maximum_broll_per_minute: int = Field(default=4, ge=0, le=60)
    maximum_sfx_per_minute: int = Field(default=6, ge=0, le=120)
    maximum_sfx_gain_db: float = Field(default=-8.0, ge=-60, le=0)


class CaptionProfile(StrictModel):
    enabled: bool = True
    max_characters_per_card: int = Field(default=28, ge=4, le=80)
    max_lines: int = Field(default=2, ge=1, le=4)


class EditingProfile(StrictModel):
    name: str = Field(min_length=1)
    version: int = Field(default=1, ge=1)
    language: str = Field(default="th", pattern=r"^[a-z]{2,3}$")
    pacing: PacingProfile = Field(default_factory=PacingProfile)
    retakes: RetakeProfile = Field(default_factory=RetakeProfile)
    creative: CreativeProfile = Field(default_factory=CreativeProfile)
    captions: CaptionProfile = Field(default_factory=CaptionProfile)

    @classmethod
    def load(cls, path: Path) -> EditingProfile:
        try:
            raw = yaml.safe_load(path.read_text(encoding="utf-8"))
        except (OSError, yaml.YAMLError) as exc:
            raise ConfigurationError(f"Could not load profile {path}: {exc}") from exc
        if not isinstance(raw, dict):
            raise ConfigurationError(f"Profile {path} must contain a YAML object")
        return cls.model_validate(raw)


class AppConfig(StrictModel):
    asset_root: Path | None = None
    model_root: Path = Path("~/.cache/video-editing-th/models")
    ffmpeg_binary: str = "ffmpeg"
    ffprobe_binary: str = "ffprobe"
    auto_editor_binary: str = "auto-editor"
    whisper_cpp_binary: str = "whisper-cli"
    project_edit_dir_name: str = Field(default="edit", pattern=r"^[A-Za-z0-9._-]+$")

    @field_validator("asset_root", "model_root", mode="before")
    @classmethod
    def expand_paths(cls, value: Any) -> Any:
        if value is None:
            return None
        return Path(value).expanduser().resolve(strict=False)

    @classmethod
    def load(cls, path: Path | None = None) -> AppConfig:
        if path is None:
            return cls()
        try:
            raw = yaml.safe_load(path.read_text(encoding="utf-8"))
        except (OSError, yaml.YAMLError) as exc:
            raise ConfigurationError(f"Could not load configuration {path}: {exc}") from exc
        if raw is None:
            raw = {}
        if not isinstance(raw, dict):
            raise ConfigurationError(f"Configuration {path} must contain a YAML object")
        return cls.model_validate(raw)
