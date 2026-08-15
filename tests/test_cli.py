import json
from pathlib import Path

import yaml
from click import unstyle
from typer.testing import CliRunner

from video_editing_th.cli import app

runner = CliRunner()


def test_root_help_lists_primary_workflows() -> None:
    result = runner.invoke(app, ["--help"])

    assert result.exit_code == 0
    assert "Thai talking-head" in result.stdout
    assert "configure" in result.stdout
    assert "config" in result.stdout
    assert "doctor" in result.stdout
    assert "project" in result.stdout
    assert "assets" in result.stdout
    assert "models" in result.stdout
    assert "plan" in result.stdout


def test_models_help_exposes_recommendation_and_cache_commands() -> None:
    result = runner.invoke(app, ["models", "--help"])

    assert result.exit_code == 0
    assert "recommend" in result.stdout
    assert "list" in result.stdout


def test_configure_help_only_exposes_machine_local_visual_choices() -> None:
    result = runner.invoke(app, ["configure", "--help"])

    assert result.exit_code == 0
    help_text = unstyle(result.stdout)
    for option in ["--broll", "--overlays", "--backgrounds", "--profile"]:
        assert option in help_text
    for removed in [
        "--sfx",
        "--music",
        "--transitions",
        "--width",
        "--height",
        "--fps",
        "--captions",
        "--no-captions",
    ]:
        assert removed not in help_text


def test_configure_non_interactive_writes_only_machine_local_defaults(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yaml"
    broll = tmp_path / "broll"
    overlays = tmp_path / "overlays"
    backgrounds = tmp_path / "backgrounds"
    broll.mkdir()
    overlays.mkdir()
    backgrounds.mkdir()

    result = runner.invoke(
        app,
        [
            "configure",
            "--config",
            str(config_path),
            "--non-interactive",
            "--broll",
            str(broll),
            "--overlays",
            str(overlays),
            "--backgrounds",
            str(backgrounds),
            "--profile",
            "thai-fast-reel",
        ],
    )

    assert result.exit_code == 0, result.stdout
    payload = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    assert payload["assets"]["broll"] == str(broll.resolve())
    assert payload["assets"]["overlays"] == str(overlays.resolve())
    assert payload["assets"]["backgrounds"] == str(backgrounds.resolve())
    assert payload["workflow"]["default_profile"] == "thai-fast-reel"
    assert "sfx" not in payload["assets"]
    assert "music" not in payload["assets"]
    assert "transitions" not in payload["assets"]
    assert "captions_enabled" not in payload["workflow"]
    assert "output" not in payload


def test_configure_interactive_only_asks_for_local_visual_folders(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yaml"
    broll = tmp_path / "broll"
    broll.mkdir()
    answers = "\n".join([str(broll), "", "", ""]) + "\n"

    result = runner.invoke(
        app,
        ["configure", "--config", str(config_path)],
        input=answers,
    )

    assert result.exit_code == 0, result.stdout
    assert "B-roll folder" in result.stdout
    assert "Overlay/graphics folder" in result.stdout
    assert "Backgrounds folder" in result.stdout
    assert "Default editing profile" in result.stdout
    for removed_prompt in [
        "Sound-effects folder",
        "Music folder",
        "Transitions folder",
        "Output width",
        "Output height",
        "Output frame rate",
        "Enable Thai captions",
    ]:
        assert removed_prompt not in result.stdout
    assert config_path.is_file()


def test_config_show_json_reads_simplified_machine_config(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yaml"
    setup = runner.invoke(
        app,
        ["configure", "--config", str(config_path), "--non-interactive"],
    )
    assert setup.exit_code == 0, setup.stdout

    result = runner.invoke(
        app,
        ["config", "show", "--config", str(config_path), "--json"],
    )

    assert result.exit_code == 0, result.stdout
    payload = json.loads(result.stdout)
    assert payload["workflow"]["default_profile"] == "thai-fast-reel"
    assert payload["workflow"]["editor_backend"] == "chatcut"
    assert "captions_enabled" not in payload["workflow"]
    assert "output" not in payload


def test_assets_help_exposes_configured_indexing() -> None:
    result = runner.invoke(app, ["assets", "--help"])

    assert result.exit_code == 0
    assert "index-configured" in result.stdout
