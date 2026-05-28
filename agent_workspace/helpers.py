from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def repo_root(start: Path | None = None) -> Path:
    current = (start or Path(__file__)).resolve()
    if current.is_file():
        current = current.parent
    for parent in [current, *current.parents]:
        if (parent / "AGENTS.md").exists() and (parent / "install.md").exists() and (parent / "agent_workspace").exists():
            return parent
    raise RuntimeError("Could not locate tflex_harness repo root")


def recipes_dir(root: Path | None = None) -> Path:
    return (root or repo_root()) / "agent_workspace" / "recipes"


def recipe_source_path(name: str, suffix: str = ".cs", root: Path | None = None) -> Path:
    if suffix not in {".cs", ".md"}:
        raise ValueError("recipe suffix must be .cs or .md")
    return recipes_dir(root) / f"{name}{suffix}"


def read_json(path: str | Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_json(path: str | Path, data: Any) -> None:
    Path(path).write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
