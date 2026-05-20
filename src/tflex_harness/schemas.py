from __future__ import annotations

DOCS_SEARCH_SCOPES = ("symbols", "types", "chm", "all")
DOCS_SEARCH_DEFAULT_LIMIT = 20
DOCS_SEARCH_MAX_LIMIT = 50


def normalize_limit(limit: int | None, default: int = DOCS_SEARCH_DEFAULT_LIMIT, maximum: int = DOCS_SEARCH_MAX_LIMIT) -> int:
    if limit is None:
        return default
    return min(max(int(limit), 1), maximum)
