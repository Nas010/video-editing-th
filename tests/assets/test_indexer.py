from pathlib import Path

from video_editing_th.assets.catalog import AssetCatalog
from video_editing_th.assets.indexer import index_assets
from video_editing_th.media import hash_file
from video_editing_th.models import MediaItem


def test_indexer_is_incremental_and_preserves_annotations(tmp_path: Path) -> None:
    asset_root = tmp_path / "library"
    asset_root.mkdir()
    source = asset_root / "broll" / "gym" / "press.mp4"
    source.parent.mkdir(parents=True)
    source.write_bytes(b"first")
    calls: list[Path] = []

    def fake_probe(path: Path, ffprobe_binary: str = "ffprobe") -> MediaItem:
        calls.append(path)
        return MediaItem(
            source_path=path,
            sha256=hash_file(path),
            size_bytes=path.stat().st_size,
            duration_seconds=6,
            width=1920,
            height=1080,
            fps=30,
            has_video=True,
            has_audio=False,
        )

    previews: list[tuple[Path, Path]] = []

    def fake_preview(path: Path, destination: Path, **_: object) -> None:
        previews.append((path, destination))
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(b"preview")

    with AssetCatalog(tmp_path / "assets.db") as catalog:
        first = index_assets(
            asset_root,
            catalog,
            tmp_path / "previews",
            probe_func=fake_probe,
            preview_func=fake_preview,
        )
        record = catalog.all()[0]
        catalog.annotate(record.id, description="Gym press", tags=["gym"])
        second = index_assets(
            asset_root,
            catalog,
            tmp_path / "previews",
            probe_func=fake_probe,
            preview_func=fake_preview,
        )
        source.write_bytes(b"second")
        third = index_assets(
            asset_root,
            catalog,
            tmp_path / "previews",
            probe_func=fake_probe,
            preview_func=fake_preview,
        )
        updated = catalog.get(record.id)

    assert first.indexed == 1 and first.unchanged == 0
    assert second.indexed == 0 and second.unchanged == 1
    assert third.updated == 1
    assert updated is not None
    assert updated.description == "Gym press"
    assert updated.tags == ["gym"]
    assert len(calls) == 2
    assert len(previews) == 2
