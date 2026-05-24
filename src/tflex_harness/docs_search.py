from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Any

from .config import HarnessConfig, load_config
from .schemas import DOCS_SEARCH_MAX_LIMIT, DOCS_SEARCH_SCOPES, normalize_limit


def _terms(query: str) -> list[str]:
    return [t.lower() for t in re.findall(r"[\w`.#:+-]+", query) if t.strip()]


def _text_score(text: str, terms: list[str]) -> float:
    if not terms:
        return 0.0
    hay = text.lower()
    score = 0.0
    for term in terms:
        if term in hay:
            score += 1.0
            if re.search(rf"\b{re.escape(term)}\b", hay):
                score += 0.5
    return score / max(len(terms), 1)


def _preview(text: str, terms: list[str], max_chars: int = 600) -> str:
    compact = re.sub(r"\s+", " ", text).strip()
    if len(compact) <= max_chars:
        return compact
    lower = compact.lower()
    positions = [lower.find(t) for t in terms if lower.find(t) >= 0]
    start = max(min(positions) - 160, 0) if positions else 0
    end = min(start + max_chars, len(compact))
    prefix = "…" if start > 0 else ""
    suffix = "…" if end < len(compact) else ""
    return prefix + compact[start:end] + suffix


@lru_cache(maxsize=4)
def _load_symbols(path: str, freshness: tuple[Any, ...] | None = None) -> tuple[dict[str, Any], ...]:
    records: list[dict[str, Any]] = []
    _ = freshness
    p = Path(path)
    if not p.exists():
        return ()
    with p.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return tuple(records)


def _file_freshness(path: Path) -> tuple[Any, ...]:
    try:
        stat = path.stat()
    except OSError:
        return (str(path), False)
    return (str(path), True, stat.st_size, stat.st_mtime_ns)


def _types_freshness(path: Path) -> tuple[Any, ...]:
    if not path.exists():
        return (str(path), False)
    entries: list[tuple[str, int, int]] = []
    for child in sorted(path.glob("*.md")):
        try:
            stat = child.stat()
        except OSError:
            continue
        entries.append((child.name, stat.st_size, stat.st_mtime_ns))
    return (str(path), True, tuple(entries))


class DocsIndex:
    def __init__(self, config: HarnessConfig | None = None) -> None:
        self.config = config or load_config()
        self._type_cache_key: tuple[Any, ...] | None = None
        self._type_cache: tuple[dict[str, str], ...] = ()
        self._chm_cache_key: tuple[Any, ...] | None = None
        self._chm_cache: tuple[dict[str, Any], ...] = ()

    def freshness(self) -> dict[str, Any]:
        return {
            "symbols": _file_freshness(self.config.symbols_jsonl),
            "types": _types_freshness(self.config.types_dir),
            "chm": _file_freshness(self.config.chm_pages_jsonl),
            "manifest": _file_freshness(self.config.manifest_json),
        }

    def symbols(self) -> tuple[dict[str, Any], ...]:
        path = self.config.symbols_jsonl
        return _load_symbols(str(path), _file_freshness(path))

    def type_pages(self) -> tuple[dict[str, str], ...]:
        key = _types_freshness(self.config.types_dir)
        if self._type_cache_key == key:
            return self._type_cache
        records: list[dict[str, str]] = []
        if self.config.types_dir.exists():
            for path in self.config.types_dir.glob("*.md"):
                try:
                    text = path.read_text(encoding="utf-8", errors="ignore")
                except OSError:
                    continue
                records.append({"path": str(path), "name": path.name, "stem": path.stem, "text": text})
        self._type_cache_key = key
        self._type_cache = tuple(records)
        return self._type_cache

    def chm_pages(self) -> tuple[dict[str, Any], ...]:
        path = self.config.chm_pages_jsonl
        key = _file_freshness(path)
        if self._chm_cache_key == key:
            return self._chm_cache
        records: list[dict[str, Any]] = []
        if path.exists():
            with path.open("r", encoding="utf-8") as fh:
                for line in fh:
                    if line.strip():
                        records.append(json.loads(line))
        self._chm_cache_key = key
        self._chm_cache = tuple(records)
        return self._chm_cache


class DocsSearch:
    def __init__(self, config: HarnessConfig | None = None) -> None:
        self.index = DocsIndex(config)
        self.config = self.index.config

    def search_symbols(self, query: str, assembly: str | None = None, limit: int = 20) -> list[dict[str, Any]]:
        limit = normalize_limit(limit)
        terms = _terms(query)
        results: list[dict[str, Any]] = []
        for rec in self.index.symbols():
            if assembly and rec.get("assembly") != assembly:
                continue
            text = " ".join(str(rec.get(k) or "") for k in ["id", "assembly", "namespace", "type", "name", "signature", "summary", "remarks"])
            score = _text_score(text, terms)
            if score <= 0:
                continue
            results.append({
                "source": "symbols.jsonl",
                "score": round(score, 4),
                "id": rec.get("id"),
                "kind": rec.get("kind"),
                "assembly": rec.get("assembly"),
                "namespace": rec.get("namespace"),
                "type": rec.get("type"),
                "name": rec.get("name"),
                "signature": rec.get("signature"),
                "summary": rec.get("summary"),
                "params": rec.get("params") or {},
                "returns": rec.get("returns"),
                "source_file": rec.get("source_file"),
            })
        results.sort(key=lambda r: (-r["score"], str(r.get("assembly") or ""), str(r.get("id") or "")))
        return results[:limit]

    def search_types(self, query: str, limit: int = 20) -> list[dict[str, Any]]:
        limit = normalize_limit(limit)
        terms = _terms(query)
        results: list[dict[str, Any]] = []
        for rec in self.index.type_pages():
            path = Path(rec["path"])
            text = rec["text"]
            file_score = _text_score(rec["name"], terms) * 2
            score = file_score + _text_score(text[:12000], terms)
            if score <= 0:
                continue
            title = text.splitlines()[0].lstrip("# ").strip() if text else rec["stem"]
            results.append({
                "source": "types",
                "score": round(score, 4),
                "path": str(path),
                "title": title,
                "preview": _preview(text, terms),
            })
        results.sort(key=lambda r: (-r["score"], r["path"]))
        return results[:limit]

    def search_chm(self, query: str, limit: int = 20) -> list[dict[str, Any]]:
        limit = normalize_limit(limit)
        terms = _terms(query)
        results: list[dict[str, Any]] = []
        for rec in self.index.chm_pages():
            text = " ".join([str(rec.get("title") or ""), str(rec.get("source_chm_path") or ""), str(rec.get("content") or "")])
            score = _text_score(text, terms)
            if score <= 0:
                continue
            results.append({
                "source": "chm_pages.jsonl",
                "score": round(score, 4),
                "id": rec.get("id"),
                "title": rec.get("title"),
                "source_chm_path": rec.get("source_chm_path"),
                "preview": _preview(str(rec.get("content") or ""), terms),
            })
        results.sort(key=lambda r: (-r["score"], str(r.get("id") or "")))
        return results[:limit]

    @staticmethod
    def _combined_results(
        symbols: list[dict[str, Any]],
        types: list[dict[str, Any]],
        chm: list[dict[str, Any]],
        limit: int,
    ) -> list[dict[str, Any]]:
        combined: list[dict[str, Any]] = []
        for scope, items in (("symbols", symbols), ("types", types), ("chm", chm)):
            for item in items:
                result = dict(item)
                result["scope"] = scope
                combined.append(result)
                if len(combined) >= limit:
                    return combined
        return combined

    def search_all(self, query: str, assembly: str | None = None, limit: int = 20) -> dict[str, Any]:
        per_scope = normalize_limit(limit)
        symbols = self.search_symbols(query, assembly=assembly, limit=per_scope)
        types = self.search_types(query, limit=per_scope)
        chm = self.search_chm(query, limit=per_scope)
        return {
            "query": query,
            "assembly": assembly,
            "scope": "all",
            "limit": per_scope,
            "max_limit": DOCS_SEARCH_MAX_LIMIT,
            "results": self._combined_results(symbols, types, chm, limit=per_scope),
            "symbols": symbols,
            "types": types,
            "chm": chm,
        }

    def search(self, query: str, scope: str = "all", assembly: str | None = None, limit: int = 20) -> dict[str, Any]:
        scope = scope.lower()
        limit = normalize_limit(limit)
        if scope == "symbols":
            symbols = self.search_symbols(query, assembly, limit)
            return {"query": query, "assembly": assembly, "scope": "symbols", "limit": limit, "max_limit": DOCS_SEARCH_MAX_LIMIT, "results": self._combined_results(symbols, [], [], limit), "symbols": symbols}
        if scope == "types":
            types = self.search_types(query, limit)
            return {"query": query, "scope": "types", "limit": limit, "max_limit": DOCS_SEARCH_MAX_LIMIT, "results": self._combined_results([], types, [], limit), "types": types}
        if scope == "chm":
            chm = self.search_chm(query, limit)
            return {"query": query, "scope": "chm", "limit": limit, "max_limit": DOCS_SEARCH_MAX_LIMIT, "results": self._combined_results([], [], chm, limit), "chm": chm}
        if scope == "all":
            return self.search_all(query, assembly, limit)
        raise ValueError(f"Unsupported docs search scope: {scope}; expected one of {', '.join(DOCS_SEARCH_SCOPES)}")
