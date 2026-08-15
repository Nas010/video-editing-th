"""Deterministic FFmpeg rough-preview rendering."""

from __future__ import annotations

import subprocess
from pathlib import Path

from .captions import build_srt
from .errors import VideoEditingError
from .models import EditPlan


def build_render_command(
    plan: EditPlan,
    output_path: Path,
    *,
    ffmpeg_binary: str = "ffmpeg",
    captions_path: Path | None = None,
    preview_height: int | None = 720,
    audio_fade_seconds: float = 0.03,
) -> list[str]:
    if not plan.structural_clips:
        raise ValueError("Cannot render an edit plan with no structural clips")

    sources: list[Path] = []
    for clip in plan.structural_clips:
        if clip.source_path not in sources:
            sources.append(clip.source_path)
    source_indices = {path: index for index, path in enumerate(sources)}

    command = [ffmpeg_binary, "-y", "-hide_banner", "-loglevel", "error"]
    for source in sources:
        command.extend(["-i", str(source)])

    filters: list[str] = []
    concat_inputs: list[str] = []
    ordered_clips = sorted(plan.structural_clips, key=lambda item: item.timeline_start)
    for index, clip in enumerate(ordered_clips):
        input_index = source_indices[clip.source_path]
        duration = clip.source_end - clip.source_start
        fade = min(audio_fade_seconds, max(0.0, duration / 4))
        video_chain = (
            f"[{input_index}:v]trim=start={clip.source_start:g}:end={clip.source_end:g},"
            "setpts=PTS-STARTPTS"
        )
        if preview_height is not None:
            video_chain += f",scale=-2:{preview_height}"
        video_chain += f"[v{index}]"
        filters.append(video_chain)
        fade_out_start = max(0.0, duration - fade)
        filters.append(
            f"[{input_index}:a]atrim=start={clip.source_start:g}:end={clip.source_end:g},"
            "asetpts=PTS-STARTPTS,"
            f"afade=t=in:st=0:d={fade:g},"
            f"afade=t=out:st={fade_out_start:g}:d={fade:g}[a{index}]"
        )
        concat_inputs.append(f"[v{index}][a{index}]")

    filters.append(
        "".join(concat_inputs) + f"concat=n={len(plan.structural_clips)}:v=1:a=1[vcat][acat]"
    )
    video_output = "vcat"
    if captions_path is not None:
        escaped = _escape_filter_path(captions_path)
        filters.append(f"[vcat]subtitles=filename='{escaped}'[vout]")
        video_output = "vout"

    command.extend(
        [
            "-filter_complex",
            ";".join(filters),
            "-map",
            f"[{video_output}]",
            "-map",
            "[acat]",
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-crf",
            "20",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-movflags",
            "+faststart",
            str(output_path),
        ]
    )
    return command


def render_rough_preview(
    plan: EditPlan,
    output_path: Path,
    *,
    ffmpeg_binary: str = "ffmpeg",
    burn_captions: bool = False,
) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    captions_path: Path | None = None
    if burn_captions and plan.captions:
        captions_path = output_path.with_suffix(".srt")
        captions_path.write_text(build_srt(plan.captions), encoding="utf-8")
    command = build_render_command(
        plan,
        output_path,
        ffmpeg_binary=ffmpeg_binary,
        captions_path=captions_path,
    )
    try:
        subprocess.run(command, check=True, capture_output=True, text=True)
    except (OSError, subprocess.CalledProcessError) as exc:
        detail = getattr(exc, "stderr", "") or str(exc)
        raise VideoEditingError(f"Rough preview render failed: {detail.strip()}") from exc
    return output_path


def _escape_filter_path(path: Path) -> str:
    resolved = str(path.resolve(strict=False))
    return resolved.replace("\\", "\\\\").replace(":", "\\:").replace("'", "\\'")
