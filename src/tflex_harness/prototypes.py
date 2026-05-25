from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from .artifacts import ArtifactStore, json_default
from .config import HarnessConfig, load_config


PROTOTYPES_ENV_VAR = "TFLEX_PROTOTYPES_DIR"
DEFAULT_PROTOTYPES_RELATIVE = "Прототипы"


@dataclass(frozen=True)
class PrototypeFile:
    id: str
    name: str
    relative_path: str
    path: Path
    category: str
    extension: str
    size: int
    sha256: str


def default_prototypes_root(config: HarnessConfig | None = None) -> Path:
    if env_root := os.environ.get(PROTOTYPES_ENV_VAR):
        return Path(env_root)
    cfg = config or load_config()
    return cfg.tflex_program_dir / DEFAULT_PROTOTYPES_RELATIVE


def scan_prototypes(root: str | Path | None = None, *, config: HarnessConfig | None = None) -> dict[str, Any]:
    source_root = Path(root) if root is not None else default_prototypes_root(config)
    source_root = source_root.resolve()
    files = [_file_to_record(path, source_root) for path in _iter_supported_files(source_root)]
    counts_by_extension: dict[str, int] = {}
    counts_by_category: dict[str, int] = {}
    for item in files:
        counts_by_extension[item.extension] = counts_by_extension.get(item.extension, 0) + 1
        counts_by_category[item.category] = counts_by_category.get(item.category, 0) + 1
    return {
        "ok": source_root.exists(),
        "root": str(source_root),
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "file_count": len(files),
        "grb_count": counts_by_extension.get(".grb", 0),
        "counts_by_extension": dict(sorted(counts_by_extension.items())),
        "counts_by_category": dict(sorted(counts_by_category.items())),
        "files": [_as_json(item) for item in files],
    }


def list_prototypes(
    root: str | Path | None = None,
    *,
    category: str | None = None,
    extension: str | None = ".grb",
    limit: int | None = None,
) -> dict[str, Any]:
    catalog = scan_prototypes(root)
    files = catalog["files"]
    if category:
        files = [item for item in files if item["category"] == category]
    if extension:
        wanted = extension if extension.startswith(".") else f".{extension}"
        files = [item for item in files if item["extension"] == wanted.lower()]
    if limit is not None:
        files = files[:limit]
    return {
        "ok": catalog["ok"],
        "root": catalog["root"],
        "count": len(files),
        "files": files,
    }


def find_prototype(
    selector: str,
    root: str | Path | None = None,
    *,
    required: bool = True,
) -> dict[str, Any] | None:
    normalized_selector = _normalize_selector(selector)
    catalog = scan_prototypes(root)
    for item in catalog["files"]:
        candidates = {
            _normalize_selector(item["id"]),
            _normalize_selector(item["relative_path"]),
            _normalize_selector(str(item["path"])),
            _normalize_selector(item["name"]),
        }
        if normalized_selector in candidates:
            return item
    if required:
        raise KeyError(f"prototype not found: {selector}")
    return None


def prototype_info(selector: str, root: str | Path | None = None) -> dict[str, Any]:
    item = find_prototype(selector, root, required=True)
    return {"ok": True, "prototype": item}


def write_catalog(catalog: dict[str, Any], output_dir: str | Path | None = None) -> Path:
    if output_dir is None:
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        out = ArtifactStore().root / "prototype_catalog" / stamp
    else:
        out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    path = out / "catalog.json"
    path.write_text(json.dumps(catalog, ensure_ascii=False, indent=2, default=json_default) + "\n", encoding="utf-8")
    return path


def scan_and_write_catalog(root: str | Path | None = None, output_dir: str | Path | None = None) -> dict[str, Any]:
    catalog = scan_prototypes(root)
    path = write_catalog(catalog, output_dir=output_dir)
    result = dict(catalog)
    result["catalog_path"] = str(path)
    return result


def _iter_supported_files(root: Path) -> list[Path]:
    if not root.exists():
        return []
    supported = {".grb", ".xml", ".txt", ".ico"}
    return sorted(
        (path for path in root.rglob("*") if path.is_file() and path.suffix.lower() in supported),
        key=lambda path: path.relative_to(root).as_posix().casefold(),
    )


def _file_to_record(path: Path, root: Path) -> PrototypeFile:
    relative_path = path.relative_to(root).as_posix()
    category = _category_from_relative(relative_path)
    return PrototypeFile(
        id=_id_from_relative(relative_path),
        name=path.name,
        relative_path=relative_path,
        path=path.resolve(),
        category=category,
        extension=path.suffix.lower(),
        size=path.stat().st_size,
        sha256=_sha256(path),
    )


def _category_from_relative(relative_path: str) -> str:
    parts = Path(relative_path).parts
    return parts[0] if len(parts) > 1 else "root"


def _id_from_relative(relative_path: str) -> str:
    path = Path(relative_path)
    without_suffix = path.with_suffix("")
    return without_suffix.as_posix()


def _as_json(item: PrototypeFile) -> dict[str, Any]:
    return {
        "id": item.id,
        "name": item.name,
        "relative_path": item.relative_path,
        "path": str(item.path),
        "category": item.category,
        "extension": item.extension,
        "size": item.size,
        "sha256": item.sha256,
    }


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _normalize_selector(value: str) -> str:
    normalized = value.replace("\\", "/").strip()
    if normalized.lower().endswith(".grb"):
        normalized = normalized[:-4]
    return normalized.casefold()
