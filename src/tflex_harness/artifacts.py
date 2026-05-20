from __future__ import annotations

import json
import re
from dataclasses import asdict, is_dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from .config import HarnessConfig, load_config


def slugify(value: str, max_len: int = 80) -> str:
    value = re.sub(r"[^A-Za-z0-9_.-]+", "_", value).strip("._-")
    return (value[:max_len] or "run")


def json_default(value: Any) -> Any:
    if isinstance(value, Path):
        return str(value)
    if is_dataclass(value):
        return asdict(value)
    raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")


class ArtifactStore:
    def __init__(self, config: HarnessConfig | None = None) -> None:
        self.config = config or load_config()
        self.root = self.config.artifacts_dir
        self.root.mkdir(parents=True, exist_ok=True)

    def create_run_dir(self, name: str) -> Path:
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        path = self.root / "runs" / f"{stamp}_{slugify(name)}"
        path.mkdir(parents=True, exist_ok=False)
        (path / "artifacts").mkdir(exist_ok=True)
        return path

    def create_tflex_doc_dir(self, name: str) -> Path:
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        path = self.root / "tflex_docs" / f"{stamp}_{slugify(name)}"
        path.mkdir(parents=True, exist_ok=False)
        return path

    @staticmethod
    def write_json(path: Path, data: Any) -> None:
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2, default=json_default) + "\n", encoding="utf-8")

    @staticmethod
    def write_text(path: Path, text: str) -> None:
        path.write_text(text, encoding="utf-8", newline="\n")
