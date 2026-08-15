"""Incremental technical indexing of local creative asset libraries."""

from __future__ import annotations

import uuid
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from ..media import hash_file, probe_media
from ..models import AssetRecord, AssetRole, MediaItem
from .catalog import AssetCatalog
from .previews import generate_contact_sheet

ASSET_EXTENSIONS = {
    ".avi",
    ".gif",
    ".jpeg",
    ".jpg",
    ".m4a",
    ".mkv",
    ".mov",
    ".mp3",
    ".mp4",
    ".png",
    ".tif",
    ".tiff",
    ".wav",
    ".webm",
}
AUDIO_EXTENSIONS = {".m4a", ".mp3", ".wav"}
IMAGE_EXTENSIONS = {".gif", ".jpeg", ".jpg", ".png", ".tif", ".tiff"}

ProbeFunc = Callable[..., MediaItem]
PreviewFunc = Callable[..., None]


@dataclass(frozen=True, slots=True)
class IndexSummary:
    indexed: int = 0
    updated: int = 0
    unchanged: int = 0
    removed: int = 0
    failed: int = 0
    errors: tuple[str, ...] = ()


def index_assets(
    asset_root: Path,
    catalog: AssetCatalog,
    preview_dir: Path,
    *,
    ffprobe_binary: str = "ffprobe",
    ffmpeg_binary: str = "ffmpeg",
    probe_func: ProbeFunc = probe_media,
    preview_func: PreviewFunc = generate_contact_sheet,
    strict: bool = True,
) -> IndexSummary:
    root = asset_root.expanduser().resolve(strict=True)
    preview_root = preview_dir.expanduser().resolve(strict=False)
    files = sorted(
        (
            path
            for path in root.rglob("*")
            if path.is_file() and path.suffix.lower() in ASSET_EXTENSIONS
        ),
        key=lambda path: path.relative_to(root).as_posix().casefold(),
    )
    indexed = updated = unchanged = failed = 0
    errors: list[str] = []

    for path in files:
        existing = catalog.get_by_path(path)
        current_hash = hash_file(path)
        if existing is not None and existing.sha256 == current_hash:
            unchanged += 1
            continue
        try:
            media = probe_func(path, ffprobe_binary=ffprobe_binary)
            role = infer_asset_role(path, root)
            asset_id = existing.id if existing else _asset_id(path)
            contact_sheet = None
            if media.has_video and media.duration_seconds > 0 and role not in {
                AssetRole.SFX,
                AssetRole.MUSIC,
            }:
                contact_sheet = preview_root / f"{asset_id}.jpg"
                preview_func(
                    path,
                    contact_sheet,
                    duration_seconds=media.duration_seconds,
                    ffmpeg_binary=ffmpeg_binary,
                )
            record = AssetRecord(
                id=asset_id,
                path=path.resolve(),
                role=role,
                sha256=media.sha256,
                size_bytes=media.size_bytes,
                duration_seconds=media.duration_seconds,
                width=media.width,
                height=media.height,
                fps=media.fps,
                has_audio=media.has_audio,
                transparent=(
                    role == AssetRole.OVERLAY
                    and path.suffix.lower() in {".png", ".mov", ".webm"}
                ),
                description=existing.description if existing else "",
                tags=existing.tags if existing else [],
                use_cases=existing.use_cases if existing else [],
                shot_type=existing.shot_type if existing else None,
                camera_motion=existing.camera_motion if existing else None,
                contact_sheet_path=(
                    contact_sheet or (existing.contact_sheet_path if existing else None)
                ),
            )
            catalog.upsert(record)
            if existing is None:
                indexed += 1
            else:
                updated += 1
        except Exception as exc:
            failed += 1
            errors.append(f"{path}: {exc}")
            if strict:
                raise

    removed = catalog.delete_missing(set(files))
    return IndexSummary(
        indexed=indexed,
        updated=updated,
        unchanged=unchanged,
        removed=removed,
        failed=failed,
        errors=tuple(errors),
    )


def infer_asset_role(path: Path, root: Path) -> AssetRole:
    relative = path.relative_to(root)
    parts = {part.casefold().replace("_", "-") for part in relative.parts[:-1]}
    suffix = path.suffix.lower()
    if parts & {"music", "songs", "soundtracks"}:
        return AssetRole.MUSIC
    if parts & {"sfx", "sound-effects", "sounds", "whooshes", "impacts", "pops"}:
        return AssetRole.SFX
    if parts & {"overlays", "overlay", "graphics", "stickers", "callouts"}:
        return AssetRole.OVERLAY
    if parts & {"transitions", "transition"}:
        return AssetRole.TRANSITION
    if parts & {"backgrounds", "background"}:
        return AssetRole.BACKGROUND
    if parts & {"broll", "b-roll", "stock"}:
        return AssetRole.BROLL
    if suffix in AUDIO_EXTENSIONS:
        return AssetRole.SFX
    if suffix in IMAGE_EXTENSIONS:
        return AssetRole.IMAGE
    return AssetRole.BROLL


def _asset_id(path: Path) -> str:
    return f"asset-{uuid.uuid5(uuid.NAMESPACE_URL, path.resolve().as_uri()).hex[:16]}"
