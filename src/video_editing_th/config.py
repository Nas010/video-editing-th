"""Typed application and editing-profile configuration."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from .errors import ConfigurationError
from .models import AssetRole

DEFAULT_SOCIAL_WIDTH = 1080
DEFAULT_SOCIAL_HEIGHT = 1920
DEFAULT_SOCIAL_FPS = 30.0


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
        raw = _read_yaml(path, label="profile")
        if not isinstance(raw, dict):
            raise ConfigurationError(f"Profile {path} must contain a YAML object")
        return cls.model_validate(raw)


class AssetLibraryConfig(StrictModel):
    """Machine-local visual folders and persistent asset-index locations."""

    broll: Path | None = None
    overlays: Path | None = None
    backgrounds: Path | None = None
    catalog_path: Path = Field(default_factory=lambda: _default_data_root() / "assets.db")
    preview_dir: Path = Field(default_factory=lambda: _default_cache_root() / "asset-previews")

    @field_validator(
        "broll",
        "overlays",
        "backgrounds",
        "catalog_path",
        "preview_dir",
        mode="before",
    )
    @classmethod
    def expand_paths(cls, value: Any) -> Any:
        return _expand_path(value)

    def configured_folders(self) -> dict[AssetRole, Path]:
        pairs = (
            (AssetRole.BROLL, self.broll),
            (AssetRole.OVERLAY, self.overlays),
            (AssetRole.BACKGROUND, self.backgrounds),
        )
        return {role: path for role, path in pairs if path is not None}


class WorkflowDefaults(StrictModel):
    """Reusable defaults that are not expected to change per project."""

    default_profile: str = Field(default="thai-fast-reel", min_length=1)
    editor_backend: Literal["chatcut"] = "chatcut"
    use_broll: bool = True
    use_overlays: bool = True
    use_motion: bool = True


class AppConfig(StrictModel):
    """Machine-local application configuration loaded outside the repository."""

    asset_root: Path | None = None
    assets: AssetLibraryConfig = Field(default_factory=AssetLibraryConfig)
    workflow: WorkflowDefaults = Field(default_factory=WorkflowDefaults)
    model_root: Path = Path("~/.cache/video-editing-th/models")
    ffmpeg_binary: str = "ffmpeg"
    ffprobe_binary: str = "ffprobe"
    auto_editor_binary: str = "auto-editor"
    whisper_cpp_binary: str = "whisper-cli"
    project_edit_dir_name: str = Field(default="edit", pattern=r"^[A-Za-z0-9._-]+$")

    @field_validator("asset_root", "model_root", mode="before")
    @classmethod
    def expand_paths(cls, value: Any) -> Any:
        return _expand_path(value)

    @classmethod
    def load(cls, path: Path | None = None) -> AppConfig:
        resolved = (path or default_config_path()).expanduser().resolve(strict=False)
        if not resolved.is_file():
            return cls()
        raw = _read_yaml(resolved, label="configuration")
        if raw is None:
            raw = {}
        if not isinstance(raw, dict):
            raise ConfigurationError(f"Configuration {resolved} must contain a YAML object")
        return cls.model_validate(_migrate_deprecated_configuration(raw))

    def save(self, path: Path | None = None) -> Path:
        """Atomically persist this configuration and return its resolved path."""

        destination = (path or default_config_path()).expanduser().resolve(strict=False)
        destination.parent.mkdir(parents=True, exist_ok=True)
        payload = yaml.safe_dump(
            self.model_dump(mode="json", exclude_none=True),
            allow_unicode=True,
            sort_keys=False,
        )
        temporary_path: Path | None = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=destination.parent,
                prefix=f".{destination.name}.",
                suffix=".tmp",
                delete=False,
            ) as temporary:
                temporary.write(payload)
                temporary.flush()
                os.fsync(temporary.fileno())
                temporary_path = Path(temporary.name)
            temporary_path.replace(destination)
        except OSError as exc:
            if temporary_path is not None:
                temporary_path.unlink(missing_ok=True)
            raise ConfigurationError(f"Could not save configuration {destination}: {exc}") from exc
        return destination


def default_config_path() -> Path:
    """Resolve the active per-user configuration path."""

    explicit = os.environ.get("VIDEO_EDITING_TH_CONFIG")
    if explicit:
        return Path(explicit).expanduser().resolve(strict=False)
    xdg_root = os.environ.get("XDG_CONFIG_HOME")
    root = Path(xdg_root).expanduser() if xdg_root else Path("~/.config").expanduser()
    return (root / "video-editing-th" / "config.yaml").resolve(strict=False)


def _default_data_root() -> Path:
    xdg_root = os.environ.get("XDG_DATA_HOME")
    root = Path(xdg_root).expanduser() if xdg_root else Path("~/.local/share").expanduser()
    return (root / "video-editing-th").resolve(strict=False)


def _default_cache_root() -> Path:
    xdg_root = os.environ.get("XDG_CACHE_HOME")
    root = Path(xdg_root).expanduser() if xdg_root else Path("~/.cache").expanduser()
    return (root / "video-editing-th").resolve(strict=False)


def _migrate_deprecated_configuration(raw: dict[str, Any]) -> dict[str, Any]:
    """Ignore fields written by the earlier over-configurable wizard."""

    migrated = dict(raw)
    migrated.pop("output", None)

    assets = migrated.get("assets")
    if isinstance(assets, dict):
        migrated_assets = dict(assets)
        for key in ("sfx", "music", "transitions"):
            migrated_assets.pop(key, None)
        migrated["assets"] = migrated_assets

    workflow = migrated.get("workflow")
    if isinstance(workflow, dict):
        migrated_workflow = dict(workflow)
        for key in (
            "use_sfx",
            "use_music",
            "use_transitions",
            "captions_enabled",
            "caption_language",
        ):
            migrated_workflow.pop(key, None)
        migrated["workflow"] = migrated_workflow

    return migrated


def _expand_path(value: Any) -> Any:
    if value is None or isinstance(value, Path):
        return value.expanduser().resolve(strict=False) if isinstance(value, Path) else None
    return Path(value).expanduser().resolve(strict=False)


def _read_yaml(path: Path, *, label: str) -> Any:
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise ConfigurationError(f"Could not load {label} {path}: {exc}") from exc
