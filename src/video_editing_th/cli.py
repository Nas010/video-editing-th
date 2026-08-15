"""Command-line interface for the Thai video editing pipeline."""

from __future__ import annotations

import json
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated

import typer
import yaml
from rich.console import Console
from rich.table import Table

from .asr_models import MODEL_SPECS, detect_hardware, installed_models, recommend_whisper_model
from .asr_models import model_path as whisper_model_path
from .assets import AssetCatalog, index_asset_folders, index_assets, search_assets
from .captions import build_caption_cues, build_srt
from .chatcut import build_chatcut_execution_manifest
from .config import (
    DEFAULT_SOCIAL_FPS,
    DEFAULT_SOCIAL_HEIGHT,
    DEFAULT_SOCIAL_WIDTH,
    AppConfig,
    EditingProfile,
    default_config_path,
)
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
config_app = typer.Typer(help="Inspect the one-time machine configuration.", no_args_is_help=True)
project_app = typer.Typer(help="Create and analyze footage projects.", no_args_is_help=True)
assets_app = typer.Typer(
    help="Index and search reusable B-roll, overlays, and backgrounds.",
    no_args_is_help=True,
)
models_app = typer.Typer(
    help="Inspect hardware and choose local whisper.cpp ASR models.",
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

app.add_typer(config_app, name="config")
app.add_typer(project_app, name="project")
app.add_typer(assets_app, name="assets")
app.add_typer(models_app, name="models")
app.add_typer(plan_app, name="plan")
app.add_typer(captions_app, name="captions")
app.add_typer(render_app, name="render")
app.add_typer(chatcut_app, name="chatcut")
app.add_typer(skill_app, name="skill")


@app.command("configure")
def configure_command(
    config_path: Annotated[Path | None, typer.Option("--config")] = None,
    non_interactive: Annotated[bool, typer.Option("--non-interactive")] = False,
    broll: Annotated[Path | None, typer.Option("--broll")] = None,
    overlays: Annotated[Path | None, typer.Option("--overlays")] = None,
    backgrounds: Annotated[Path | None, typer.Option("--backgrounds")] = None,
    profile: Annotated[str | None, typer.Option("--profile")] = None,
    use_broll: Annotated[bool | None, typer.Option("--use-broll/--no-use-broll")] = None,
    use_overlays: Annotated[
        bool | None,
        typer.Option("--use-overlays/--no-use-overlays"),
    ] = None,
    use_motion: Annotated[bool | None, typer.Option("--use-motion/--no-use-motion")] = None,
) -> None:
    """Create or update the one-time machine-local visual-asset configuration."""

    destination = _config_destination(config_path)
    current = AppConfig.load(destination)

    if non_interactive:
        selected_broll = _resolve_optional_directory(
            broll if broll is not None else current.assets.broll,
            "B-roll folder",
        )
        selected_overlays = _resolve_optional_directory(
            overlays if overlays is not None else current.assets.overlays,
            "Overlay/graphics folder",
        )
        selected_backgrounds = _resolve_optional_directory(
            backgrounds if backgrounds is not None else current.assets.backgrounds,
            "Backgrounds folder",
        )
        selected_profile = profile or current.workflow.default_profile
    else:
        selected_broll = _selected_or_prompted_directory(
            broll,
            current.assets.broll,
            "B-roll folder",
        )
        selected_overlays = _selected_or_prompted_directory(
            overlays,
            current.assets.overlays,
            "Overlay/graphics folder",
        )
        selected_backgrounds = _selected_or_prompted_directory(
            backgrounds,
            current.assets.backgrounds,
            "Backgrounds folder",
        )
        selected_profile = profile or typer.prompt(
            "Default editing profile",
            default=current.workflow.default_profile,
        )

    assets = current.assets.model_copy(
        update={
            "broll": selected_broll,
            "overlays": selected_overlays,
            "backgrounds": selected_backgrounds,
        }
    )
    workflow = current.workflow.model_copy(
        update={
            "default_profile": selected_profile,
            "use_broll": use_broll if use_broll is not None else current.workflow.use_broll,
            "use_overlays": (
                use_overlays if use_overlays is not None else current.workflow.use_overlays
            ),
            "use_motion": (use_motion if use_motion is not None else current.workflow.use_motion),
        }
    )
    configured = current.model_copy(update={"assets": assets, "workflow": workflow})
    written = configured.save(destination)
    typer.echo(f"Saved configuration: {written}")


@config_app.command("path")
def config_path_command(
    config_path: Annotated[Path | None, typer.Option("--config")] = None,
) -> None:
    """Print the active machine-local configuration path."""

    typer.echo(str(_config_destination(config_path)))


@config_app.command("show")
def config_show_command(
    config_path: Annotated[Path | None, typer.Option("--config")] = None,
    as_json: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Print the resolved machine configuration."""

    config = AppConfig.load(_config_destination(config_path))
    payload = config.model_dump(mode="json", exclude_none=True)
    if as_json:
        typer.echo(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        typer.echo(yaml.safe_dump(payload, allow_unicode=True, sort_keys=False).rstrip())


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


@models_app.command("recommend")
def models_recommend(
    name_only: Annotated[
        bool,
        typer.Option("--name-only", help="Print only the recommended model name."),
    ] = False,
) -> None:
    """Recommend a multilingual whisper.cpp model for this machine."""

    hardware = detect_hardware()
    recommendation = recommend_whisper_model(hardware)
    if name_only:
        typer.echo(recommendation.default_model)
        return

    table = Table(title="Local Thai ASR recommendation")
    table.add_column("Item")
    table.add_column("Value")
    table.add_row("OS", hardware.os_name)
    table.add_row("Architecture", hardware.architecture)
    table.add_row(
        "Memory",
        f"{hardware.memory_gib:.1f} GiB" if hardware.memory_gib is not None else "unknown",
    )
    table.add_row("Default model", recommendation.default_model)
    table.add_row("Accuracy mode", recommendation.accuracy_model)
    table.add_row(
        "Full large-v3 recommended",
        "yes" if recommendation.full_large_v3_recommended else "no",
    )
    table.add_row("Why", recommendation.rationale)
    console.print(table)


@models_app.command("list")
def models_list(
    config_path: Annotated[Path | None, typer.Option("--config")] = None,
) -> None:
    """List supported local whisper.cpp models and installed cache state."""

    config = AppConfig.load(config_path)
    present = set(installed_models(config.model_root))
    table = Table(title=f"whisper.cpp models — {config.model_root}")
    table.add_column("Model")
    table.add_column("Disk")
    table.add_column("Installed")
    table.add_column("Notes")
    for name, spec in MODEL_SPECS.items():
        size = (
            f"{spec.disk_mib / 1024:.1f} GiB" if spec.disk_mib >= 1024 else f"{spec.disk_mib} MiB"
        )
        table.add_row(name, size, "yes" if name in present else "no", spec.notes)
    console.print(table)


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
    resolved_model_path = model_path
    if resolved_model_path is None and backend.strip().lower() in {
        "auto",
        "whisper.cpp",
        "whisper-cpp",
        "cpp",
    }:
        recommendation = recommend_whisper_model(detect_hardware())
        cached = whisper_model_path(config.model_root, recommendation.default_model)
        if cached.is_file():
            resolved_model_path = cached

    media = probe_media(media_path, ffprobe_binary=config.ffprobe_binary)
    transcriber = select_backend(
        backend,
        model_path=resolved_model_path,
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
    catalog_path: Annotated[Path | None, typer.Option("--catalog")] = None,
    preview_dir: Annotated[Path | None, typer.Option("--preview-dir")] = None,
    config_path: Annotated[Path | None, typer.Option("--config")] = None,
    strict: Annotated[bool, typer.Option("--strict/--continue-on-error")] = True,
) -> None:
    """Incrementally index technical metadata and contact sheets."""

    config = AppConfig.load(config_path)
    with AssetCatalog(catalog_path or config.assets.catalog_path) as catalog:
        summary = index_assets(
            asset_root,
            catalog,
            preview_dir or config.assets.preview_dir,
            ffprobe_binary=config.ffprobe_binary,
            ffmpeg_binary=config.ffmpeg_binary,
            strict=strict,
        )
    typer.echo(json.dumps(asdict(summary), ensure_ascii=False, default=list, indent=2))


@assets_app.command("index-configured")
def assets_index_configured(
    config_path: Annotated[Path | None, typer.Option("--config")] = None,
    strict: Annotated[bool, typer.Option("--strict/--continue-on-error")] = True,
) -> None:
    """Index every visual folder saved by the one-time configuration."""

    config = AppConfig.load(config_path)
    folders = config.assets.configured_folders()
    with AssetCatalog(config.assets.catalog_path) as catalog:
        if folders:
            summary = index_asset_folders(
                folders,
                catalog,
                config.assets.preview_dir,
                ffprobe_binary=config.ffprobe_binary,
                ffmpeg_binary=config.ffmpeg_binary,
                strict=strict,
            )
        elif config.asset_root is not None:
            summary = index_assets(
                config.asset_root,
                catalog,
                config.assets.preview_dir,
                ffprobe_binary=config.ffprobe_binary,
                ffmpeg_binary=config.ffmpeg_binary,
                strict=strict,
            )
        else:
            raise typer.BadParameter(
                "No visual asset folders are configured. Run 'video-editing-th configure' first."
            )
    typer.echo(json.dumps(asdict(summary), ensure_ascii=False, default=list, indent=2))


@assets_app.command("annotate")
def assets_annotate(
    asset_id: Annotated[str, typer.Argument()],
    description: Annotated[str, typer.Option("--description")],
    catalog_path: Annotated[Path | None, typer.Option("--catalog")] = None,
    config_path: Annotated[Path | None, typer.Option("--config")] = None,
    tag: Annotated[list[str] | None, typer.Option("--tag")] = None,
    use_case: Annotated[list[str] | None, typer.Option("--use-case")] = None,
    shot_type: Annotated[str | None, typer.Option("--shot-type")] = None,
    camera_motion: Annotated[str | None, typer.Option("--camera-motion")] = None,
) -> None:
    """Persist Codex-authored descriptions, tags, and suggested use cases."""

    config = AppConfig.load(config_path)
    with AssetCatalog(catalog_path or config.assets.catalog_path) as catalog:
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
    catalog_path: Annotated[Path | None, typer.Option("--catalog")] = None,
    config_path: Annotated[Path | None, typer.Option("--config")] = None,
    role: Annotated[AssetRole | None, typer.Option("--role")] = None,
    orientation: Annotated[str | None, typer.Option("--orientation")] = None,
    limit: Annotated[int, typer.Option("--limit", min=1, max=100)] = 10,
) -> None:
    """Return a compact candidate shortlist for Codex visual verification."""

    config = AppConfig.load(config_path)
    with AssetCatalog(catalog_path or config.assets.catalog_path) as catalog:
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
    width: Annotated[int | None, typer.Option("--width", min=2)] = None,
    height: Annotated[int | None, typer.Option("--height", min=2)] = None,
    fps: Annotated[float | None, typer.Option("--fps", min=1)] = None,
) -> None:
    """Export ordered operations that Codex executes through ChatCut MCP/browser."""

    plan = read_model(plan_path, EditPlan)
    manifest = build_chatcut_execution_manifest(
        plan,
        composition_width=width if width is not None else DEFAULT_SOCIAL_WIDTH,
        composition_height=height if height is not None else DEFAULT_SOCIAL_HEIGHT,
        fps=fps if fps is not None else DEFAULT_SOCIAL_FPS,
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


def _config_destination(path: Path | None) -> Path:
    return (path or default_config_path()).expanduser().resolve(strict=False)


def _selected_or_prompted_directory(
    selected: Path | None,
    current: Path | None,
    label: str,
) -> Path | None:
    if selected is not None:
        return _resolve_optional_directory(selected, label)
    answer = typer.prompt(
        label,
        default=str(current) if current is not None else "",
        show_default=current is not None,
    )
    return _resolve_optional_directory(answer, label)


def _resolve_optional_directory(value: Path | str | None, label: str) -> Path | None:
    if value is None or not str(value).strip():
        return None
    raw = Path(value).expanduser()
    try:
        resolved = raw.resolve(strict=True)
    except OSError as exc:
        raise typer.BadParameter(f"{label} does not exist: {raw}") from exc
    if not resolved.is_dir():
        raise typer.BadParameter(f"{label} is not a directory: {resolved}")
    return resolved


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
