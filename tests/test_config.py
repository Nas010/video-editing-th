from pathlib import Path

import pytest
from pydantic import ValidationError

from video_editing_th.config import (
    DEFAULT_SOCIAL_FPS,
    DEFAULT_SOCIAL_HEIGHT,
    DEFAULT_SOCIAL_WIDTH,
    AppConfig,
    AssetLibraryConfig,
    EditingProfile,
    WorkflowDefaults,
    default_config_path,
)
from video_editing_th.models import AssetRole


def test_profile_loads_and_expands_defaults(tmp_path: Path) -> None:
    profile_path = tmp_path / "profile.yaml"
    profile_path.write_text(
        """
name: test-profile
version: 1
language: th
pacing:
  intra_thought_target_ms: 90
  sentence_target_ms: 240
  topic_target_ms: 420
  word_handle_ms: 85
  maximum_audio_overlap_ms: 25
retakes:
  maximum_gap_seconds: 15
  similarity_threshold: 0.72
  prefer_latest_complete: true
  preserve_uncertain: true
creative:
  maximum_punch_ins_per_minute: 5
  maximum_broll_per_minute: 4
  maximum_sfx_per_minute: 6
  maximum_sfx_gain_db: -8
captions:
  enabled: true
  max_characters_per_card: 28
  max_lines: 2
""".strip(),
        encoding="utf-8",
    )

    profile = EditingProfile.load(profile_path)

    assert profile.name == "test-profile"
    assert profile.language == "th"
    assert profile.pacing.sentence_target_ms == 240
    assert profile.captions.max_lines == 2


def test_profile_rejects_non_monotonic_pause_targets() -> None:
    with pytest.raises(ValidationError, match="pause targets"):
        EditingProfile.model_validate(
            {
                "name": "bad",
                "version": 1,
                "language": "th",
                "pacing": {
                    "intra_thought_target_ms": 300,
                    "sentence_target_ms": 200,
                    "topic_target_ms": 100,
                    "word_handle_ms": 80,
                    "maximum_audio_overlap_ms": 20,
                },
            }
        )


def test_machine_config_contains_only_local_visual_asset_choices() -> None:
    assert {"sfx", "music", "transitions"}.isdisjoint(AssetLibraryConfig.model_fields)
    assert {
        "captions_enabled",
        "caption_language",
        "use_sfx",
        "use_music",
        "use_transitions",
    }.isdisjoint(WorkflowDefaults.model_fields)
    assert "output" not in AppConfig.model_fields
    assert (DEFAULT_SOCIAL_WIDTH, DEFAULT_SOCIAL_HEIGHT, DEFAULT_SOCIAL_FPS) == (
        1080,
        1920,
        30.0,
    )


def test_app_config_expands_user_paths(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    fake_home = tmp_path / "home"
    fake_home.mkdir()
    monkeypatch.setenv("HOME", str(fake_home))

    config = AppConfig.model_validate(
        {
            "asset_root": "~/assets",
            "model_root": "~/models",
            "assets": {
                "broll": "~/broll",
                "overlays": "~/overlays",
                "backgrounds": "~/backgrounds",
                "catalog_path": "~/catalog/assets.db",
                "preview_dir": "~/previews",
            },
            "ffmpeg_binary": "ffmpeg-custom",
        }
    )

    assert config.asset_root == fake_home / "assets"
    assert config.model_root == fake_home / "models"
    assert config.assets.broll == fake_home / "broll"
    assert config.assets.overlays == fake_home / "overlays"
    assert config.assets.backgrounds == fake_home / "backgrounds"
    assert config.assets.catalog_path == fake_home / "catalog" / "assets.db"
    assert config.assets.preview_dir == fake_home / "previews"
    assert config.ffmpeg_binary == "ffmpeg-custom"


def test_app_config_expands_default_model_root() -> None:
    config = AppConfig()

    assert config.model_root.is_absolute()
    assert config.assets.catalog_path.is_absolute()
    assert config.assets.preview_dir.is_absolute()
    assert "~" not in str(config.model_root)


def test_default_config_path_honors_environment(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    explicit = tmp_path / "custom" / "config.yaml"
    monkeypatch.setenv("VIDEO_EDITING_TH_CONFIG", str(explicit))

    assert default_config_path() == explicit.resolve()

    monkeypatch.delenv("VIDEO_EDITING_TH_CONFIG")
    xdg = tmp_path / "xdg"
    monkeypatch.setenv("XDG_CONFIG_HOME", str(xdg))

    assert default_config_path() == (xdg / "video-editing-th" / "config.yaml").resolve()


def test_app_config_save_and_default_load_round_trip(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    config_path = tmp_path / "config" / "config.yaml"
    monkeypatch.setenv("VIDEO_EDITING_TH_CONFIG", str(config_path))
    broll = tmp_path / "broll"
    overlays = tmp_path / "overlays"
    backgrounds = tmp_path / "backgrounds"
    broll.mkdir()
    overlays.mkdir()
    backgrounds.mkdir()

    config = AppConfig(
        assets=AssetLibraryConfig(
            broll=broll,
            overlays=overlays,
            backgrounds=backgrounds,
        ),
        workflow=WorkflowDefaults(default_profile="thai-fast-reel"),
    )

    written = config.save()
    loaded = AppConfig.load()

    assert written == config_path.resolve()
    assert loaded == config
    assert loaded.assets.configured_folders() == {
        AssetRole.BROLL: broll.resolve(),
        AssetRole.OVERLAY: overlays.resolve(),
        AssetRole.BACKGROUND: backgrounds.resolve(),
    }


def test_app_config_load_migrates_deprecated_native_chatcut_and_output_fields(
    tmp_path: Path,
) -> None:
    config_path = tmp_path / "legacy.yaml"
    config_path.write_text(
        """
assets:
  broll: /tmp/broll
  sfx: /tmp/sfx
  music: /tmp/music
  transitions: /tmp/transitions
workflow:
  default_profile: thai-fast-reel
  use_sfx: true
  use_music: true
  use_transitions: true
  captions_enabled: false
  caption_language: th
output:
  width: 720
  height: 1280
  fps: 24
""".strip(),
        encoding="utf-8",
    )

    loaded = AppConfig.load(config_path)
    rewritten = loaded.save(config_path)
    saved = rewritten.read_text(encoding="utf-8")

    assert loaded.assets.broll == Path("/tmp/broll")
    assert "sfx:" not in saved
    assert "music:" not in saved
    assert "transitions:" not in saved
    assert "captions_enabled" not in saved
    assert "output:" not in saved


def test_app_config_load_without_saved_file_uses_defaults(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("VIDEO_EDITING_TH_CONFIG", str(tmp_path / "missing.yaml"))

    config = AppConfig.load()

    assert config.workflow.default_profile == "thai-fast-reel"
    assert config.workflow.editor_backend == "chatcut"
    assert config.workflow.use_broll is True
    assert config.workflow.use_overlays is True
    assert config.workflow.use_motion is True
