import json
from pathlib import Path

import yaml
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


def test_configure_non_interactive_writes_machine_local_defaults(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yaml"
    broll = tmp_path / "broll"
    overlays = tmp_path / "overlays"
    broll.mkdir()
    overlays.mkdir()

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
            "--profile",
            "thai-fast-reel",
            "--width",
            "1080",
            "--height",
            "1920",
            "--fps",
            "30",
            "--no-captions",
        ],
    )

    assert result.exit_code == 0, result.stdout
    payload = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    assert payload["assets"]["broll"] == str(broll.resolve())
    assert payload["assets"]["overlays"] == str(overlays.resolve())
    assert payload["workflow"]["default_profile"] == "thai-fast-reel"
    assert payload["workflow"]["captions_enabled"] is False
    assert payload["output"] == {"width": 1080, "height": 1920, "fps": 30.0}


def test_configure_interactive_asks_for_asset_folders(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yaml"
    broll = tmp_path / "broll"
    broll.mkdir()
    answers = "\n".join(
        [
            str(broll),
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
        ]
    ) + "\n"

    result = runner.invoke(
        app,
        ["configure", "--config", str(config_path)],
        input=answers,
    )

    assert result.exit_code == 0, result.stdout
    assert "B-roll folder" in result.stdout
    assert "Overlay/graphics folder" in result.stdout
    assert "Sound-effects folder" in result.stdout
    assert config_path.is_file()


def test_config_show_json_reads_the_saved_default(tmp_path: Path) -> None:
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
    assert payload["output"]["width"] == 1080


def test_assets_help_exposes_configured_indexing() -> None:
    result = runner.invoke(app, ["assets", "--help"])

    assert result.exit_code == 0
    assert "index-configured" in result.stdout
