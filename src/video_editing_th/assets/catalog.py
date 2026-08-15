"""SQLite-backed persistent asset catalog."""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Iterator
from datetime import datetime
from pathlib import Path
from types import TracebackType

from ..models import AssetRecord, AssetRole

CATALOG_SCHEMA_VERSION = 1


class AssetCatalog:
    """Own the SQLite schema and canonical AssetRecord persistence."""

    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path.expanduser().resolve(strict=False)
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self._connection = sqlite3.connect(self.database_path)
        self._connection.row_factory = sqlite3.Row
        self._connection.execute("PRAGMA foreign_keys = ON")
        self._connection.execute("PRAGMA journal_mode = WAL")
        self._migrate()

    def __enter__(self) -> AssetCatalog:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        if exc_type is None:
            self._connection.commit()
        else:
            self._connection.rollback()
        self.close()

    @property
    def connection(self) -> sqlite3.Connection:
        return self._connection

    @property
    def schema_version(self) -> int:
        row = self._connection.execute(
            "SELECT value FROM metadata WHERE key = 'schema_version'"
        ).fetchone()
        if row is None:
            raise RuntimeError("Asset catalog schema metadata is missing")
        return int(row["value"])

    def close(self) -> None:
        self._connection.close()

    def _migrate(self) -> None:
        self._connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS metadata (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS assets (
                id TEXT PRIMARY KEY,
                schema_version INTEGER NOT NULL,
                path TEXT NOT NULL UNIQUE,
                role TEXT NOT NULL,
                sha256 TEXT NOT NULL,
                size_bytes INTEGER NOT NULL,
                duration_seconds REAL,
                width INTEGER,
                height INTEGER,
                fps REAL,
                has_audio INTEGER NOT NULL,
                transparent INTEGER NOT NULL,
                orientation TEXT NOT NULL,
                description TEXT NOT NULL,
                tags_json TEXT NOT NULL,
                use_cases_json TEXT NOT NULL,
                shot_type TEXT,
                camera_motion TEXT,
                contact_sheet_path TEXT,
                indexed_at TEXT NOT NULL
            );

            CREATE VIRTUAL TABLE IF NOT EXISTS assets_fts USING fts5(
                asset_id UNINDEXED,
                path,
                description,
                tags,
                use_cases,
                tokenize = 'unicode61 remove_diacritics 0'
            );
            """
        )
        row = self._connection.execute(
            "SELECT value FROM metadata WHERE key = 'schema_version'"
        ).fetchone()
        if row is None:
            self._connection.execute(
                "INSERT INTO metadata(key, value) VALUES('schema_version', ?)",
                (str(CATALOG_SCHEMA_VERSION),),
            )
        elif int(row["value"]) != CATALOG_SCHEMA_VERSION:
            raise RuntimeError(
                "Unsupported asset catalog schema "
                f"{row['value']}; expected {CATALOG_SCHEMA_VERSION}"
            )
        self._connection.commit()

    def upsert(self, asset: AssetRecord) -> None:
        payload = _asset_to_row(asset)
        columns = ", ".join(payload)
        placeholders = ", ".join("?" for _ in payload)
        updates = ", ".join(f"{column}=excluded.{column}" for column in payload if column != "id")
        self._connection.execute(
            f"INSERT INTO assets ({columns}) VALUES ({placeholders}) "
            f"ON CONFLICT(id) DO UPDATE SET {updates}",
            tuple(payload.values()),
        )
        self._sync_fts(asset)
        self._connection.commit()

    def _sync_fts(self, asset: AssetRecord) -> None:
        self._connection.execute("DELETE FROM assets_fts WHERE asset_id = ?", (asset.id,))
        self._connection.execute(
            "INSERT INTO assets_fts(asset_id, path, description, tags, use_cases) "
            "VALUES (?, ?, ?, ?, ?)",
            (
                asset.id,
                str(asset.path),
                asset.description,
                " ".join(asset.tags),
                " ".join(asset.use_cases),
            ),
        )

    def get(self, asset_id: str) -> AssetRecord | None:
        row = self._connection.execute("SELECT * FROM assets WHERE id = ?", (asset_id,)).fetchone()
        return _row_to_asset(row) if row is not None else None

    def get_by_path(self, path: Path) -> AssetRecord | None:
        resolved = path.expanduser().resolve(strict=False)
        row = self._connection.execute(
            "SELECT * FROM assets WHERE path = ?", (str(resolved),)
        ).fetchone()
        return _row_to_asset(row) if row is not None else None

    def all(self) -> list[AssetRecord]:
        rows = self._connection.execute(
            "SELECT * FROM assets ORDER BY path COLLATE NOCASE"
        ).fetchall()
        return [_row_to_asset(row) for row in rows]

    def iter_all(self) -> Iterator[AssetRecord]:
        for row in self._connection.execute("SELECT * FROM assets ORDER BY path COLLATE NOCASE"):
            yield _row_to_asset(row)

    def annotate(
        self,
        asset_id: str,
        *,
        description: str,
        tags: list[str] | None = None,
        use_cases: list[str] | None = None,
        shot_type: str | None = None,
        camera_motion: str | None = None,
    ) -> AssetRecord:
        current = self.get(asset_id)
        if current is None:
            raise KeyError(f"Unknown asset: {asset_id}")
        updated = current.model_copy(
            update={
                "description": description.strip(),
                "tags": _unique_clean(tags if tags is not None else current.tags),
                "use_cases": _unique_clean(
                    use_cases if use_cases is not None else current.use_cases
                ),
                "shot_type": shot_type if shot_type is not None else current.shot_type,
                "camera_motion": (
                    camera_motion if camera_motion is not None else current.camera_motion
                ),
            }
        )
        self.upsert(updated)
        return updated

    def delete_missing(self, existing_paths: set[Path]) -> int:
        normalized = {str(path.expanduser().resolve(strict=False)) for path in existing_paths}
        rows = self._connection.execute("SELECT id, path FROM assets").fetchall()
        removed = 0
        for row in rows:
            if row["path"] in normalized:
                continue
            self._connection.execute("DELETE FROM assets_fts WHERE asset_id = ?", (row["id"],))
            self._connection.execute("DELETE FROM assets WHERE id = ?", (row["id"],))
            removed += 1
        self._connection.commit()
        return removed


def _unique_clean(values: list[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for raw in values:
        value = raw.strip()
        key = value.casefold()
        if value and key not in seen:
            result.append(value)
            seen.add(key)
    return result


def _asset_to_row(asset: AssetRecord) -> dict[str, object]:
    return {
        "id": asset.id,
        "schema_version": asset.schema_version,
        "path": str(asset.path.expanduser().resolve(strict=False)),
        "role": asset.role.value,
        "sha256": asset.sha256,
        "size_bytes": asset.size_bytes,
        "duration_seconds": asset.duration_seconds,
        "width": asset.width,
        "height": asset.height,
        "fps": asset.fps,
        "has_audio": int(asset.has_audio),
        "transparent": int(asset.transparent),
        "orientation": asset.orientation,
        "description": asset.description,
        "tags_json": json.dumps(asset.tags, ensure_ascii=False),
        "use_cases_json": json.dumps(asset.use_cases, ensure_ascii=False),
        "shot_type": asset.shot_type,
        "camera_motion": asset.camera_motion,
        "contact_sheet_path": str(asset.contact_sheet_path) if asset.contact_sheet_path else None,
        "indexed_at": asset.indexed_at.isoformat(),
    }


def _row_to_asset(row: sqlite3.Row) -> AssetRecord:
    return AssetRecord(
        schema_version=row["schema_version"],
        id=row["id"],
        path=Path(row["path"]),
        role=AssetRole(row["role"]),
        sha256=row["sha256"],
        size_bytes=row["size_bytes"],
        duration_seconds=row["duration_seconds"],
        width=row["width"],
        height=row["height"],
        fps=row["fps"],
        has_audio=bool(row["has_audio"]),
        transparent=bool(row["transparent"]),
        orientation=row["orientation"],
        description=row["description"],
        tags=json.loads(row["tags_json"]),
        use_cases=json.loads(row["use_cases_json"]),
        shot_type=row["shot_type"],
        camera_motion=row["camera_motion"],
        contact_sheet_path=(Path(row["contact_sheet_path"]) if row["contact_sheet_path"] else None),
        indexed_at=datetime.fromisoformat(row["indexed_at"]),
    )
