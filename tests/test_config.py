from pathlib import Path

import pytest
from pydantic import ValidationError

from video_editing_th.config import AppConfig, EditingProfile


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


def test_app_config_expands_user_paths(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    fake_home = tmp_path / "home"
    fake_home.mkdir()
    monkeypatch.setenv("HOME", str(fake_home))

    config = AppConfig.model_validate(
        {
            "asset_root": "~/assets",
            "model_root": "~/models",
            "ffmpeg_binary": "ffmpeg-custom",
        }
    )

    assert config.asset_root == fake_home / "assets"
    assert config.model_root == fake_home / "models"
    assert config.ffmpeg_binary == "ffmpeg-custom"


def test_app_config_expands_default_model_root() -> None:
    config = AppConfig()

    assert config.model_root.is_absolute()
    assert "~" not in str(config.model_root)
