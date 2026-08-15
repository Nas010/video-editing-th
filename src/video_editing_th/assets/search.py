"""Fast asset shortlist retrieval from persisted descriptions and tags."""

from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass

from ..models import AssetRecord, AssetRole
from .catalog import AssetCatalog


@dataclass(frozen=True, slots=True)
class AssetSearchResult:
    asset: AssetRecord
    score: float
    matched_terms: tuple[str, ...]


def search_assets(
    catalog: AssetCatalog,
    query: str,
    *,
    role: AssetRole | None = None,
    orientation: str | None = None,
    limit: int = 10,
) -> list[AssetSearchResult]:
    if limit < 1:
        raise ValueError("limit must be positive")
    terms = _query_terms(query)
    candidates = _candidate_ids(catalog, terms, max(limit * 8, 40))
    assets: Iterable[AssetRecord | None]
    if terms:
        assets = (catalog.get(asset_id) for asset_id in candidates)
    else:
        assets = catalog.all()

    results: list[AssetSearchResult] = []
    for asset in assets:
        if asset is None:
            continue
        if role is not None and asset.role != role:
            continue
        if orientation is not None and asset.orientation != orientation:
            continue
        haystack = " ".join(
            [str(asset.path), asset.description, *asset.tags, *asset.use_cases]
        ).casefold()
        matched = tuple(term for term in terms if term in haystack)
        if terms and not matched:
            continue
        coverage = len(matched) / len(terms) if terms else 0.0
        description_bonus = sum(term in asset.description.casefold() for term in terms) * 0.08
        tag_bonus = sum(term in " ".join(asset.tags).casefold() for term in terms) * 0.12
        exact_phrase_bonus = 0.25 if query.strip().casefold() in haystack and query.strip() else 0.0
        score = coverage + description_bonus + tag_bonus + exact_phrase_bonus
        results.append(AssetSearchResult(asset=asset, score=score, matched_terms=matched))

    results.sort(key=lambda result: (-result.score, str(result.asset.path).casefold()))
    return results[:limit]


def _candidate_ids(catalog: AssetCatalog, terms: list[str], limit: int) -> list[str]:
    if not terms:
        return []
    expression = " OR ".join(f'"{term.replace(chr(34), chr(34) * 2)}"' for term in terms)
    try:
        rows = catalog.connection.execute(
            "SELECT asset_id FROM assets_fts WHERE assets_fts MATCH ? "
            "ORDER BY bm25(assets_fts) LIMIT ?",
            (expression, limit),
        ).fetchall()
    except Exception:
        rows = []
    if rows:
        return [str(row["asset_id"]) for row in rows]

    clauses = " OR ".join(
        "lower(description || ' ' || tags_json || ' ' || use_cases_json || ' ' || path) LIKE ?"
        for _ in terms
    )
    parameters = [f"%{term.casefold()}%" for term in terms]
    rows = catalog.connection.execute(
        f"SELECT id AS asset_id FROM assets WHERE {clauses} ORDER BY path LIMIT ?",
        (*parameters, limit),
    ).fetchall()
    return [str(row["asset_id"]) for row in rows]


def _query_terms(query: str) -> list[str]:
    terms = re.findall(r"[\w\u0E00-\u0E7F]+", query.casefold(), flags=re.UNICODE)
    unique: list[str] = []
    for term in terms:
        if len(term) < 2 or term in unique:
            continue
        unique.append(term)
    return unique
