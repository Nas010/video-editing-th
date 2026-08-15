from pathlib import Path

from video_editing_th.assets.catalog import AssetCatalog
from video_editing_th.assets.search import search_assets
from video_editing_th.models import AssetRecord, AssetRole


def make_asset(
    path: Path,
    asset_id: str,
    description: str,
    tags: list[str],
    *,
    role: AssetRole = AssetRole.BROLL,
    width: int = 1920,
    height: int = 1080,
) -> AssetRecord:
    return AssetRecord(
        id=asset_id,
        path=path,
        role=role,
        sha256=asset_id[-1] * 64,
        size_bytes=100,
        duration_seconds=5,
        width=width,
        height=height,
        description=description,
        tags=tags,
    )


def test_search_ranks_relevant_asset_and_applies_filters(tmp_path: Path) -> None:
    with AssetCatalog(tmp_path / "assets.db") as catalog:
        catalog.upsert(
            make_asset(
                tmp_path / "dumbbell.mp4",
                "asset-a",
                "Athlete performs an incline dumbbell press in a gym",
                ["strength", "chest", "hypertrophy"],
            )
        )
        catalog.upsert(
            make_asset(
                tmp_path / "beach.mp4",
                "asset-b",
                "Wide beach sunset with calm waves",
                ["travel", "sunset"],
            )
        )
        catalog.upsert(
            make_asset(
                tmp_path / "check.webm",
                "asset-c",
                "Animated green check mark",
                ["correct", "success"],
                role=AssetRole.OVERLAY,
                width=1080,
                height=1920,
            )
        )

        results = search_assets(
            catalog,
            "strength training dumbbell chest",
            role=AssetRole.BROLL,
            orientation="landscape",
            limit=5,
        )

    assert [result.asset.id for result in results] == ["asset-a"]
    assert results[0].score > 0
