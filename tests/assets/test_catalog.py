from pathlib import Path

from video_editing_th.assets.catalog import AssetCatalog
from video_editing_th.models import AssetRecord, AssetRole


def asset(path: Path, *, role: AssetRole = AssetRole.BROLL, description: str = "") -> AssetRecord:
    return AssetRecord(
        id=f"asset-{path.stem}",
        path=path,
        role=role,
        sha256=("a" if role == AssetRole.BROLL else "b") * 64,
        size_bytes=100,
        duration_seconds=5.0,
        width=1920,
        height=1080,
        description=description,
    )


def test_catalog_migrates_and_round_trips_asset(tmp_path: Path) -> None:
    database = tmp_path / "assets.db"
    record = asset(tmp_path / "gym.mp4", description="Dumbbell press in a gym")

    with AssetCatalog(database) as catalog:
        catalog.upsert(record)
        restored = catalog.get(record.id)
        schema_version = catalog.schema_version

    assert schema_version == 1
    assert restored == record


def test_annotation_updates_searchable_fields_without_changing_hash(tmp_path: Path) -> None:
    record = asset(tmp_path / "gym.mp4")

    with AssetCatalog(tmp_path / "assets.db") as catalog:
        catalog.upsert(record)
        updated = catalog.annotate(
            record.id,
            description="Close-up incline dumbbell press",
            tags=["gym", "chest", "strength"],
            use_cases=["protein and hypertrophy explanations"],
        )

    assert updated.sha256 == record.sha256
    assert updated.description == "Close-up incline dumbbell press"
    assert updated.tags == ["gym", "chest", "strength"]
