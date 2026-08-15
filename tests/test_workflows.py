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
            TranscriptWord(text="à¸ªà¸§à¸±à¸ªà¸”à¸µ", start=0.0, end=0.5),
            TranscriptWord(text="à¸„à¸£à¸±à¸š", start=0.5, end=0.8),
            TranscriptWord(text="à¸ªà¸§à¸±à¸ªà¸”à¸µ", start=2.0, end=2.5),
            TranscriptWord(text="à¸„à¸£à¸±à¸š", start=2.5, end=2.8),
        ],
        segments=[
            TranscriptSegment(id="s1", start=0.0, end=0.8, text="à¸ªà¸§à¸±à¸ªà¸”à¸µà¸„à¸£à¸±à¸š", word_indices=[0, 1]),
            TranscriptSegment(id="s2", start=2.0, end=2.8, text="à¸ªà¸§à¸±à¸ªà¸”à¸µà¸„à¸£à¸±à¸š", word_indices=[2, 3]),
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
        words=[TranscriptWord(text="à¸ªà¸§à¸±à¸ªà¸”à¸µà¸„à¸£à¸±à¸š", start=0.0, end=0.8)],
        segments=[
            TranscriptSegment(
                id="s1",
                start=0.0,
                end=0.8,
                text="à¸ªà¸§à¸±à¸ªà¸”à¸µà¸„à¸£à¸±à¸š",
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
            str(transcript_diŠKˆ‹K\›Ùš[H‹ˆİŠ›Ùš[JKˆ‹K[İ]]‹ˆİŠİ]]
KˆKˆ
B‚ˆ\ÜÙ\™\İ[™^]ØÛÙHOH™\İ[œİİ]ˆ\]YH™XYÛ[Ù[
İ]]Y][ŠBˆ\ÜÙ\ØİYK^›ÜˆİYH[ˆ\]Y˜Ø\[Ûœ×HOHÈ¸.*¸.)ø.,x.*¸.%8.-x.!8.(ø.,x.&ˆ—B‚‚™Yˆ\İÛØØ]WÜÚÚ[ÜÛİ\˜ÙWÜİ\Ü×İÚY[Ù]WÙš[\Ê\Ü]ˆ]
HOˆ›Û™N‚ˆœ›ÛHšY[×ÙY][™×İœÚÚ[Ú[œİ[[\ÜØØ]WÜÚÚ[ÜÛİ\˜ÙB‚ˆ[œİ[YH\Ü]ÈœÚ\™HˆÈšY[ËYY][™Ë]ˆÈœÚÚ[‚ˆ[œİ[Y›ZÙ\Š\™[ÏUYJBˆ
[œİ[YÈ”ÒÒS›YŠKÜš]Wİ^
ˆ‹KKW›˜[YNˆšY[ËYY][™Ë]™\ØÜš\[Ûˆ\ÙHÚ[ˆ\İ[™Ë—‹KKWˆ‹ˆ[˜ÛÙ[™ÏH]‹N‹ˆ
B‚ˆØØ]YHØØ]WÜÚÚ[ÜÛİ\˜ÙJˆ™\ÜÚ]ÜWÜ›Ûİ]\Ü]È››İXKXÚXÚÛİ]‹ˆ[œİ[Ü™Yš^]\Ü]ˆ
B‚ˆ\ÜÙ\ØØ]YOH[œİ[Y‚‚™Yˆ\İØ\ÜÙ]×Ú[™^ØÛÛ[X[™ÜÙ\šX[^™\×ÜÛİ×Üİ[[X\J\Ü]ˆ]
HOˆ›Û™N‚ˆ\ÜÙ]Ü›ÛİH\Ü]È˜\ÜÙ]È‚ˆ
\ÜÙ]Ü›ÛİÈ˜œ›ÛŠK›ZÙ\Š\™[ÏUYJBˆ
\ÜÙ]Ü›ÛİÈ˜œ›ÛˆÈ˜Û\›[İˆŠKÜš]WØ]\Êˆ˜\ÜÙ]ŠBˆ˜ZÙWÜ›Ø™HH\Ü]È™™œ›Ø™H‚ˆ›Ø™WÜ^[ØYHÂˆœİ™X[\ÈˆÂˆÂˆ˜ÛÙX×İ\HˆšY[È‹ˆ˜ÛÙX×Û˜[YHˆš‹ˆÚYˆLˆšZYÚˆNLŒˆ˜]™×Ùœ˜[YWÜ˜]HˆŒÌÌH‹ˆKˆÈ˜ÛÙX×İ\Hˆ˜]Y[È‹˜ÛÙX×Û˜[YHˆ˜XXÈŸKˆKˆ™›Ü›X]ˆÈ™\˜][ÛˆˆŒ‹ŒŸKˆBˆ˜ZÙWÜ›Ø™KÜš]Wİ^
ˆˆÈKİ\Ü‹Øš[‹Ù[ˆ]ÛŒ×ˆ‚ˆš[\ÜœÛÛ—ˆ‚ˆˆœš[
œÛÛ‹™[\ÊÚœÛÛ‹™[\Ê›Ø™WÜ^[ØY
_JJWˆ‹ˆ[˜ÛÙ[™ÏH]‹N‹ˆ
Bˆ˜ZÙWÜ›Ø™K˜Ú[Ù
ÍÍMJBˆ˜ZÙWÙ™›\YÈH\Ü]È™™›\YÈ‚ˆ˜ZÙWÙ™›\YËÜš]Wİ^
ˆˆÈKİ\Ü‹Øš[‹Ù[ˆ]ÛŒ×ˆ‚ˆš[\Ü]X‹Ş\×ˆ‚ˆœ]X‹”]
Ş\Ë˜\™İ–ËLWJKİXÚ

Wˆ‹ˆ[˜ÛÙ[™ÏH]‹N‹ˆ
Bˆ˜ZÙWÙ™›\YË˜Ú[Ù
ÍÍMJBˆÛÛ™šYÈH\Ü]È˜ÛÛ™šYËX[[‚ˆÛÛ™šYËÜš]Wİ^
ˆˆ™™œ›Ø™WØš[˜\NˆÙ˜ZÙWÜ›Ø™_W™™›\Y×Øš[˜\NˆÙ˜ZÙWÙ™›\YßWˆ‹ˆ[˜ÛÙ[™ÏH]‹N‹ˆ
BˆØ][ÙÈH\Ü]È˜Ø][ÙË™ˆ‚ˆ™]šY]ÜÈH\Ü]Èœ™]šY]ÜÈ‚‚ˆ™\İ[H[›™\‹š[›ÚÙJˆ\ˆÂˆ˜\ÜÙ]È‹ˆš[™^‹ˆİŠ\ÜÙ]Ü›Ûİ
Kˆ‹KXØ][ÙÈ‹ˆİŠØ][ÙÊKˆ‹K\™]šY]ËY\ˆ‹ˆİŠ™]šY]ÜÊKˆ‹KXÛÛ™šYÈ‹ˆİŠÛÛ™šYÊKˆKˆ
B‚ˆ\ÜÙ\™\İ[™^]ØÛÙHOH™\İ[œİİ]ˆ^[ØYHœÛÛ‹›ØYÊ™\İ[œİİ]
Bˆ\ÜÙ\^[ØYÈš[™^Y—HOHB