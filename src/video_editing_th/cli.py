"""Command-line interface for the Thai video editing pipeline."""

from __future__ import annotations

import json
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table

from .assets import AssetCatalog, index_assets, search_assets
from .captions import build_caption_cues, build_srt
from .chatcut import build_chatcut_execution_manifest
from .config import AppConfig, EditingProfile
from .doctor import run_doctor
from .io import read_model, write_model_atomic
from .media import inventory_folder, probe_media
from .models import (
    AssetRole,
    EditPlan,
    ProjectManifest,
    ProjectStatus,
    RetakeAnalysis,
    Transcript,
)
from .packing import pack_transcript, render_packed_markdown
from .planning import validate_edit_plan
from .project import initialize_project
from .render import render_rough_preview
from .retakes import find_retake_groups
from .skill_install import install_skill_links, locate_skill_source
from .transcription.base import TranscriptionOptions
from .transcription.service import select_backend
from .transcription.thai_quality import normalize_thai_transcript, validate_thai_transcript

console = Console()

app = typer.Typer(
    name="video-editing-th",
    help="Thai talking-head analysis, asset retrieval, edit planning, and ChatCut execution.",
    no_args_is_help=True,
)
project_app = typer.Typer(help="Create and analyze footage projects.", no_args_is_help=True)
assets_app = typer.Typer(
    help="Index and search reusable B-roll, overlays, and SFX.",
    no_args_is_help=True,
)
plan_app = typer.Typer(help="Validate canonical edit plans.", no_args_is_help=True)
captions_app = typer.Typer(
    help="Build Thai captions from validated transcripts.",
    no_args_is_help=True,
)
render_app = typer.Typer(help="Render deterministic local review previews.", no_args_is_help=True)
chatcut_app = typer.Typer(
    help="Export deterministic operations for Codex-controlled ChatCut.",
    no_args_is_help=True,
)
skill_app = typer.Typer(help="Install the repository Codex skill.", no_args_is_help=True)

app.add_typer(project_app, name="project")
app.add_typer(assets_app, name="assets")
app.add_typer(plan_app, name="plan")
app.add_typer(captions_app, name="captions")
app.add_typer(render_app, name="render")
app.add_typer(chatcut_app, name="chatcut")
app.add_typer(skill_app, name="skill")


@app.command("doctor")
def doctor_command(
    config_path: Annotated[
        Path | None,
        typer.Option("--config", help="Optional application YAML configuration."),
    ] = None,
) -> None:
    """Report dependencies without changing the machine."""

    report = run_doctor(AppConfig.load(config_path))
    table = Table(title="video-editing-th doctor")
    table.add_column("Check")
    table.add_column("Required")
    table.add_column("Status")
    table.add_column("Detail")
    for check in report.checks:
        table.add_row(
            check.name,
            "yes" if check.required else "no",
            "available" if check.available else "missing",
            check.detail,
        )
    console.print(table)
    console.print("READY" if report.ready else "NOT READY")
    if not report.ready:
        raise typer.Exit(code=1)


@project_app.command("init")
def project_init(
    root: Annotated[Path, typer.Argument(help="Folder containing untouched source footage.")],
    profile: Annotated[Path, typer.Option("--profile", help="Editing profile YAML.")],
    edit_dir_name: Annotated[
        str,
        typer.Option("--edit-dir-name", help="Generated output directory name."),
    ] = "edit",
) -> None:
    """Create an idempotent project workspace next to source footage."""

    manifest = initialize_project(root, profile, edit_dir_name=edit_dir_name)
    path = manifest.edit_dir / "project.json"
    typer.echo(str(path))


@project_app.command("inventory")
def project_inventory(
    root: Annotated[Path, typer.Argument(help="Initialized footage project folder.")],
    config_path: Annotated[Path | None, typer.Option("--config")] = None,
    edit_dir_name: Annotated[str, typer.Option("--edit-dir-name")] = "edit",
) -> None:
    """Hash and probe all source media, excluding generated output."""

    config = AppConfig.load(config_path)
    resolved_root = root.expanduser().resolve(strict=True)
    manifest_path = resolved_root / edit_dir_name / "project.json"
    manifest = read_model(manifest_path, ProjectManifest)
    media = inventory_folder(
        resolved_root,
        ffprobe_binary=config.ffprobe_binary,
        edit_dir_name=edit_dir_name,
    )
    updated = manifest.model_copy(
        update={
            "status": ProjectStatus.INVENTORIED,
            "media": media,
            "updated_at": datetime.now(UTC),
        }
    )
    write_model_atomic(manifest_path, updated)
    typer.echo(f"Inventoried {len(media)} media file(s): {manifest_path}")


@app.command("transcribe")
def transcribe_command(
    media_path: Annotated[Path, typer.Argument(help="Source video or audio file.")],
    backend: Annotated[str, typer.Option("--backend")] = "auto",
    model_path: Annotated[Path | None, typer.Option("--model")] = None,
    imported_path: Annotated[Path | None, typer.Option("--imported-transcript")] = None,
    output: Annotated[Path | None, typer.Option("--output")] = None,
    quality_output: Annotated[Path | None, typer.Option("--quality-output")] = None,
    language: Annotated[str, typer.Option("--language")] = "th",
    prompt: Annotated[str | None, typer.Option("--prompt")] = None,
    config_path: Annotated[Path | None, typer.Option("--config")] = None,
) -> None:
    """Create a canonical transcript and enforce the Thai quality gate."""

    config = AppConfig.load(config_path)
    media = probe_media(media_path, ffprobe_binary=config.ffprobe_binary)
    transcriber = select_backend(
        backend,
        model_path=model_path,
        imported_path=imported_path,
        whisper_binary=config.whisper_cpp_binary,
        ffmpeg_binary=config.ffmpeg_binary,
    )
    transcript = normalize_thai_transcript(
        transcriber.transcribe(
            media,
            TranscriptionOptions(language=language, prompt=prompt),
        )
    )
    quality = validate_thai_transcript(transcript)
    transcript_path = output or (
        media.source_path.parent
        / config.project_edit_dir_name
        / "transcripts"
        / f"{media.source_path.stem}.json"
    )
    report_path = quality_output or transcript_path.with_name(
        f"{transcript_path.stem}.quality.json"
    )
    write_model_atomic(transcript_path, transcript)
    write_model_atomic(report_path, quality)
    typer.echo(str(transcript_path))
    typer.echo(str(report_path))
    if not quality.safe_for_automatic_editing:
        typer.echo("Thai transcript failed the automatic-editing quality gate.", err=True)
        raise typer.Exit(code=2)


@app.command("analyze")
def analyze_command(
    transcript_path: Annotated[Path, typer.Argument(help="Canonical transcript JSON.")],
    profile: Annotated[Path, typer.Option("--profile")],
    output_dir: Annotated[Path, typer.Option("--output-dir")],
    break_seconds: Annotated[float, typer.Option("--break-seconds")] = 0.5,
) -> None:
    """Pack a transcript and create conservative retake candidates for Codex review."""

    transcript = read_model(transcript_path, Transcript)
    quality = validate_thai_transcript(transcript)
    if not quality.safe_for_automatic_editing:
        raise typer.BadParameter(
            "Transcript did not pass the Thai quality gate; preserve footage and fix ASR first."
        )
    editing_profile = EditingProfile.load(profile)
    output_dir.mkdir(parents=True, exist_ok=True)
    phrases = pack_transcript(transcript, break_seconds=break_seconds)
    packed_path = output_dir / "takes_packed.md"
    packed_path.write_text(
        render_packed_markdown(transcript_path.stem, phrases),
        encoding="utf-8",
    )
    analysis = RetakeAnalysis(
        media_sha256=transcript.media_sha256,
        profile_name=editing_profile.name,
        groups=find_retake_groups(transcript, editing_profile),
    )
    retakes_path = output_dir / "retake-groups.json"
    write_model_atomic(retakes_path, analysis)
    typer.echo(str(packed_path))
    typer.echo(str(retakes_path))


@assets_app.command("index")
def assets_index(
    asset_root: Annotated[Path, typer.Argument(help="Reusable asset-library root.")],
    catalog_path: Annotated[Path, typer.Option("--catalog")],
    preview_dir: Annotated[Path, typer.Option("--preview-dir")],
    config_path: Annotated[Path | None, typer.Option("--config")] = None,
    strict: Annotated[bool, typer.Option("--strict/--continue-on-error")] = True,
) -> None:
    """Incrementally index technical metadata and contact sheets."""

    config = AppConfig.load(config_path)
    with AssetCatalog(catalog_path) as catalog:
        summary = index_assets(
            asset_root,
            catalog,
            preview_dir,
            ffprobe_binary=config.ffprobe_binary,
            ffmpeg_binary=config.ffmpeg_binary,
            strict=strict,
        )
    typer.echo(json.dumps(asdict(summary), ensure_ascii=False, default=list, indent=2))


@assets_app.command("annotate")
def assets_annotate(
    catalog_path: Annotated[Path, typer.Option("--catalog")],
    asset_id: Annotated[str, typer.Argument()],
    description: Annotated[str, typer.Option("--description")],
    tag: Annotated[list[str] | None, typer.Option("--tag")] = None,
    use_case: Annotated[list[str] | None, typer.Option("--use-case")] = None,
    shot_type: Annotated[str | None, typer.Option("--shot-type")] = None,
    camera_motion: Annotated[str | None, typer.Option("--camera-motion")] = None,
) -> None:
    """Persist Codex-authored descriptions, tags, and suggested use cases."""

    with AssetCatalog(catalog_path) as catalog:
        asset = catalog.annotate(
            asset_id,
            description=description,
            tags=tag,
            use_cases=use_case,
            shot_type=shot_type,
            camera_motion=camera_motion,
        )
    typer.echo(asset.model_dump_json(indent=2))


@assets_app.command("search")
def assets_search(
    query: Annotated[str, typer.Argument()],
    catalog_path: Annotated[Path, typer.Option("--catalog")],
    role: Annotated[AssetRole | None, typer.Option("--role")] = None,
    orientation: Annotated[str | None, typer.Option("--orientation")] = None,
    limit: Annotated[int, typer.Option("--limit", min=1, max=100)] = 10,
) -> None:
    """Return a compact candidate shortlist for Codex visual verification."""

    with AssetCatalog(catalog_path) as catalog:
        results = search_assets(
            catalog,
            query,
            role=role,
            orientation=orientation,
            limit=limit,
        )
    payload = [
        {
            "score": result.score,
            "matched_terms": result.matched_terms,
            "asset": result.asset.model_dump(mode="json"),
        }
        for result in results
    ]
    typer.echo(json.dumps(payload, ensure_ascii=False, indent=2))


@plan_app.command("validate")
def plan_validate(
    plan_path: Annotated[Path, typer.Argument()],
    transcripts: Annotated[Path, typer.Option("--transcripts")],
    profile: Annotated[Path, typer.Option("--profile")],
) -> None:
    """Validate word boundaries, operation limits, and review warnings."""

    plan = read_model(plan_path, EditPlan)
    result = validate_edit_plan(
        plan,
        _load_transcripts(transcripts),
        EditingProfile.load(profile),
    )
    for warning in result.warnings:
        typer.echo(f"WARNING: {warning}")
    for error in result.errors:
        typer.echo(f"ERROR: {error}", err=True)
    if not result.valid:
        raise typer.Exit(code=2)
    typer.echo("VALID")


@captions_app.command("build")
def captions_build(
    plan_path: Annotated[Path, typer.Argument()],
    transcripts: Annotated[Path, typer.Option("--transcripts")],
    profile: Annotated[Path, typer.Option("--profile")],
    output: Annotated[Path, typer.Option("--output")],
    srt_output: Annotated[Path | None, typer.Option("--srt-output")] = None,
) -> None:
    """Map corrected Thai words onto the edited output timeline."""

    plan = read_model(plan_path, EditPlan)
    transcript_map = _load_transcripts(transcripts)
    cues = build_caption_cues(plan, transcript_map, EditingProfile.load(profile))
    updated = plan.model_copy(update={"captions": cues})
    write_model_atomic(output, updated)
    if srt_output is not None:
        srt_output.parent.mkdir(parents=True, exist_ok=True)
        srt_output.write_text(build_srt(cues), encoding="utf-8")
        typer.echo(str(srt_output))
    typer.echo(str(output))


@render_app.command("preview")
def render_preview(
    plan_path: Annotated[Path, typer.Argument()],
    output: Annotated[Path, typer.Option("--output")],
    burn_captions: Annotated[bool, typer.Option("--burn-captions/--no-burn-captions")] = False,
    config_path: Annotated[Path | None, typer.Option("--config")] = None,
) -> None:
    """Render a deterministic rough structural preview with FFmpeg."""

    config = AppConfig.load(config_path)
    rendered = render_rough_preview(
        read_model(plan_path, EditPlan),
        output,
        ffmpeg_binary=config.ffmpeg_binary,
        burn_captions=burn_captions,
    )
    typer.echo(str(rendered))


@chatcut_app.command("export")
def chatcut_export(
    plan_path: Annotated[Path, typer.Argument()],
    output: Annotated[Path, typer.Option("--output")],
    width: Annotated[int, typer.Option("--width", min=2)] = 1080,
    height: Annotated[int, typer.Option("--height", min=2)] = 1920,
    fps: Annotated[float, typer.Option("--fps", min=1)] = 30.0,
) -> None:
    """Export ordered operations that Codex executes through ChatCut MCP/browser."""

    plan = read_model(plan_path, EditPlan)
    manifest = build_chatcut_execution_manifest(
        plan,
        composition_width=width,
        composition_height=height,
        fps=fps,
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(manifest.model_dump_json(indent=2) + "\n", encoding="utf-8")
    typer.echo(str(output))


@skill_app.command("install")
def skill_install(
    source: Annotated[Path | None, typer.Option("--source")] = None,
    codex_home: Annotated[
        Path,
        typer.Option("--codex-home", envvar="CODEX_HOME"),
    ] = Path("~/.codex"),
    agents_home: Annotated[Path, typer.Option("--agents-home")] = Path("~/.agents"),
) -> None:
    """Register the complete skill directory for Codex and compatible agents."""

    skill_source = source or _default_skill_source()
    destinations = install_skill_links(
        skill_source,
        codex_home=codex_home,
        agents_home=agents_home,
    )
    for destination in destinations:
        typer.echo(str(destination))


def _load_transcripts(directory: Path) -> dict[str, Transcript]:
    resolved = directory.expanduser().resolve(strict=True)
    transcripts: dict[str, Transcript] = {}
    for path in sorted(resolved.glob("*.json")):
        try:
            transcript = read_model(path, Transcript)
        except Exception:
            continue
        transcripts[transcript.media_sha256] = transcript
    if not transcripts:
        raise typer.BadParameter(f"No canonical transcript JSON files found in {resolved}")
    return transcripts


def _default_skill_source() -> Path:
    try:
        return locate_skill_source(repository_root=Path(__file__).resolve().parents[2])
    except FileNotFoundError as exc:
        raise typer.BadParameter(
            "Could not locate the bundled skill; pass --source explicitly."
        ) from exc


def main() -> None:
    app()


if __name__ == "__main__":
    main()
