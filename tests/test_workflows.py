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


def test_chatcut_export_command_writes_stable_manifest(tmp_path: Path) -> None:
    source = tmp_path / "source.mov"
    plan_path = tmp_path / "plan.json"
    output = tmp_path / "chatcut.json"
    plan = EditPlan(
        project_id="p1",
        profile_name="test",
        structural_clips=[
            ClipDecision(
                id="c1",
                source_path=source,
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

    result = runner.invoke(app, ["chatcut", "export", str(plan_path), "--output", str(output)])

    assert result.exit_code == 0, result.stdout
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["project_id"] == "p1"
    assert any(operation["action"] == "place_source_clip" for operation in payload["operations"])


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


def test_analyze_command_writes_packed_transcript_and_versioned_retake_file(
    tmp_path: Path,
) -> None:
    from video_editing_th.models import Transcript, TranscriptSegment, TranscriptWord

    profile = tmp_path / "profile.yaml"
    write_profile(profile)
    transcript = Transcript(
        media_sha256="b" * 64,
        language="th",
        backend="fixture",
        model="fixture",
        words=[
            TranscriptWord(text="สวัสดี", start=0.0, end=0.5),
            TranscriptWord(text="ครับ", start=0.5, end=0.8),
            TranscriptWord(text="สวัสดี", start=2.0, end=2.5),
            TranscriptWord(text="ครับ", start=2.5, end=2.8),
        ],
        segments=[
            TranscriptSegment(id="s1", start=0.0, end=0.8, text="สวัสดีครับ", word_indices=[0, 1]),
            TranscriptSegment(id="s2", start=2.0, end=2.8, text="สวัสดีครับ", word_indices=[2, 3]),
        ],
    )
    transcript_path = tmp_path / "transcript.json"
    write_model_atomic(transcript_path, transcript)
    output_dir = tmp_path / "analysis"

    result = runner.invoke(
        app,
        [
            "analyze",
            str(transcript_path),
            "--profile",
            str(profile),
            "--output-dir",
            str(output_dir),
        ],
    )

    assert result.exit_code == 0, result.stdout
    assert (output_dir / "takes_packed.md").is_file()
    payload = json.loads((output_dir / "retake-groups.json").read_text(encoding="utf-8"))
    assert payload["schema_version"] == 1
    assert payload["media_sha256"] == "b" * 64


def test_captions_build_command_writes_updated_plan(tmp_path: Path) -> None:
    from video_editing_th.models import Transcript, TranscriptSegment, TranscriptWord

    profile = tmp_path / "profile.yaml"
    write_profile(profile)
    transcript_dir = tmp_path / "transcripts"
    transcript_dir.mkdir()
    transcript = Transcript(
        media_sha256="a" * 64,
        language="th",
        backend="fixture",
        model="fixture",
        words=[TranscriptWord(text="สวัสดีครับ", start=0.0, end=0.8)],
        segments=[
            TranscriptSegment(
                id="s1",
                start=0.0,
                end=0.8,
                text="สวัสดีครับ",
                word_indices=[0],
            )
        ],
    )
    write_model_atomic(transcript_dir / "a.json", transcript)
    plan = EditPlan(
        project_id="p1",
        profile_name="test",
        structural_clips=[
            ClipDecision(
                id="c1",
                source_path=tmp_path / "source.mov",
                source_sha256="a" * 64,
                source_start=0,
                source_end=1,
                timeline_start=0,
                timeline_end=1,
                reason="keep",
                confidence=1,
            )
        ],
    )
    plan_path = tmp_path / "plan.json"
    output = tmp_path / "plan-with-captions.json"
    write_model_atomic(plan_path, plan)

    result = runner.invoke(
        app,
        [
            "captions",
            "build",
            str(plan_path),
            "--transcripts",
            str(transcript_dir),
            "--profile",
            str(profile),
            "--output",
            str(output),
        ],
    )

    assert result.exit_code == 0, result.stdout
    updated = read_model(output, EditPlan)
    assert [cue.text for cue in updated.captions] == ["สวัสดีครับ"]


def test_locate_skill_source_supports_wheel_data_files(tmp_path: Path) -> None:
    from video_editing_th.skill_install import locate_skill_source

    installed = tmp_path / "share" / "video-editing-th" / "skill"
    installed.mkdir(parents=True)
    (installed / "SKILL.md").write_text(
        "---\nname: video-editing-th\ndescription: Use when testing.\n---\n",
        encoding="utf-8",
    )

    located = locate_skill_source(
        repository_root=tmp_path / "not-a-checkout",
        install_prefix=tmp_path,
    )

    assert located == installed


def test_assets_index_command_serializes_slots_summary(tmp_path: Path) -> None:
    asset_root = tmp_path / "assets"
    (asset_root / "broll").mkdir(parents=True)
    (asset_root / "broll" / "clip.mov").write_bytes(b"asset")
    fake_probe = tmp_path / "ffprobe"
    probe_payload = {
        "streams": [
            {
                "codec_type": "video",
                "codec_name": "h264",
                "width": 1080,
                "height": 1920,
                "avg_frame_rate": "30/1",
            },
            {"codec_type": "audio", "codec_name": "aac"},
        ],
        "format": {"duration": "2.0"},
    }
    fake_probe.write_text(
        "#!/usr/bin/env python3\n"
        "import json\n"
        f"print(json.dumps({json.dumps(probe_payload)}))\n",
        encoding="utf-8",
    )
    fake_probe.chmod(0o755)
    fake_ffmpeg = tmp_path / "ffmpeg"
    fake_ffmpeg.write_text(
        "#!/usr/bin/env python3\n"
        "import pathlib, sys\n"
        "pathlib.Path(sys.argv[-1]).touch()\n",
        encoding="utf-8",
    )
    fake_ffmpeg.chmod(0o755)
    config = tmp_path / "config.yaml"
    config.write_text(
        f"ffprobe_binary: {fake_probe}\nffmpeg_binary: {fake_ffmpeg}\n",
        encoding="utf-8",
    )
    catalog = tmp_path / "catalog.db"
    previews = tmp_path / "previews"

    result = runner.invoke(
        app,
        [
            "assets",
            "index",
            str(asset_root),
            "--catalog",
            str(catalog),
            "--preview-dir",
            str(previews),
            "--config",
            str(config),
        ],
    )

    assert result.exit_code == 0, result.stdout
    payload = json.loads(result.stdout)
    assert payload["indexed"] == 1
