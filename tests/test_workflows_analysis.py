import json
from pathlib import Path

from typer.testing import CliRunner

from video_editing_th.cli import app
from video_editing_th.io import read_model, write_model_atomic
from video_editing_th.models import (
    ClipDecision,
    EditPlan,
    Transcript,
    TranscriptSegment,
    TranscriptWord,
)
from video_editing_th.skill_install import locate_skill_source

runner = CliRunner()


def write_profile(path: Path) -> None:
    path.write_text("name: test\nversion: 1\nlanguage: th\n", encoding="utf-8")


def transcript(words: list[tuple[str, float, float]]) -> Transcript:
    transcript_words = [
        TranscriptWord(text=text, start=start, end=end) for text, start, end in words
    ]
    return Transcript(
        media_sha256="a" * 64,
        language="th",
        backend="fixture",
        model="fixture",
        words=transcript_words,
        segments=[
            TranscriptSegment(
                id=f"s{index}",
                start=start,
                end=end,
                text=text,
                word_indices=[index],
            )
            for index, (text, start, end) in enumerate(words)
        ],
    )


def test_analyze_writes_packed_transcript_and_versioned_retakes(tmp_path: Path) -> None:
    profile = tmp_path / "profile.yaml"
    write_profile(profile)
    source = transcript([("สวัสดีครับ", 0.0, 0.8), ("สวัสดีครับ", 2.0, 2.8)])
    transcript_path = tmp_path / "transcript.json"
    write_model_atomic(transcript_path, source)
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
    assert payload["media_sha256"] == "a" * 64


def test_captions_build_writes_updated_plan(tmp_path: Path) -> None:
    profile = tmp_path / "profile.yaml"
    write_profile(profile)
    transcript_dir = tmp_path / "transcripts"
    transcript_dir.mkdir()
    write_model_atomic(
        transcript_dir / "a.json",
        transcript([("สวัสดีครับ", 0.0, 0.8)]),
    )
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
    assert [cue.text for cue in read_model(output, EditPlan).captions] == ["สวัสดีครับ"]


def test_locate_skill_source_supports_wheel_data_files(tmp_path: Path) -> None:
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
