"""Persistent indexing and retrieval for B-roll, overlays, and audio assets."""

from .catalog import AssetCatalog
from .indexer import IndexSummary, index_assets
from .search import AssetSearchResult, search_assets

__all__ = ["AssetCatalog", "AssetSearchResult", "IndexSummary", "index_assets", "search_assets"]
