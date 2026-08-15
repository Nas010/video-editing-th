import json
from pathlib import Path

from typer.testing import CliRunner

from video_editing_th.cli import app
from video_editing_th.io import read_model, write_model_atomic
from video_editing_th.models import ClipDecision, EditPlan, ProjectManifest

runner = CliRunner()


def write_profile(path: Path) -> None:
    path.write_text("name: test\nversion: 1\nlanguage: th\n", encoding="utf-8")


def test_project_init_command_creates_manifest(tmp_path: Path) -> None:
    profile = tmp_path / "profile.yaml"
    write_profile(profile)

    result = runner.invoke(app, ["project", "init", str(tmp_path), "--profile", str(profile)])

    assert result.exit_code == 0, result.stdout
    manifest_path = tmp_path / "edit" / "project.json"
    manifest = read_model(manifest_path, ProjectManifest)
    assert manifest.profile_name == "test"
    assert str(manifest_path) in result.stdout


def test_chatcut_export_command_uses_fixed_social_vertical_defaults(tmp_path: Path) -> None:
    plan_path = tmp_path / "plan.json"
    output = tmp_path / "chatcut.json"
    plan = EditPlan(
        project_id="p1",
        profile_name="test",
        structural_clips=[
            ClipDecision(
                id="c1",
                source_path=tmp_path / "source.mov",
                source_sha256="a" * 64,
                source_start=0,
                source_end=2,
                timeline_start=0,
                timeline_end=2,
                reason="keep",
                confidence=1,
            )
        ],
    )
    write_model_atomic(plan_path, plan)

    result = runner.invoke(
        app,
        ["chatcut", "export", str(plan_path), "--output", str(output)],
    )

    assert result.exit_code == 0, result.stdout
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["project_id"] == "p1"
    assert payload["composition_width"] == 1080
    assert payload["composition_height"] == 1920
    assert payload["fps"] == 30.0
    assert any(item["action"] == "place_source_clip" for item in payload["operations"])


def test_chatcut_export_allows_an_explicit_per_project_format_override(tmp_path: Path) -> None:
    plan_path = tmp_path / "plan.json"
    output = tmp_path / "chatcut.json"
    write_model_atomic(
        plan_path,
        EditPlan(project_id="p1", profile_name="test"),
    )

    result = runner.invoke(
        app,
        [
            "chatcut",
            "export",
            str(plan_path),
            "--output",
            str(output),
            "--width",
            "1920",
            "--height",
            "1080",
            "--fps",
            "24",
        ],
    )

    assert result.exit_code == 0, result.stdout
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["composition_width"] == 1920
    assert payload["composition_height"] == 1080
    assert payload["fps"] == 24.0


def test_skill_install_command_links_codex_and_agents_targets(tmp_path: Path) -> None:
    source = tmp_path / "skill-source"
    source.mkdir()
    (source / "SKILL.md").write_text(
        "---\nname: x\ndescription: Use when testing.\n---\n",
        encoding="utf-8",
    )
    codex_home = tmp_path / "codex"
    agents_home = tmp_path / "agents"

    result = runner.invoke(
        app,
        [
            "skill",
            "install",
            "--source",
            str(source),
            "--codex-home",
            str(codex_home),
            "--agents-home",
            str(agents_home),
        ],
    )

    assert result.exit_code == 0, result.stdout
    assert (codex_home / "skills" / "video-editing-th").is_symlink()
    assert (agents_home / "skills" / "video-editing-th").is_symlink()


def test_root_help_lists_complete_pipeline_commands() -> None:
    result = runner.invoke(app, ["--help"])

    assert result.exit_code == 0, result.stdout
    for command in ["transcribe", "analyze", "captions", "render", "chatcut", "skill"]:
        assert command in result.stdout
