from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .artifacts import json_default
from .config import HarnessConfig, load_config


def utc_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def append_jsonl(path: str | Path, record: dict[str, Any]) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("a", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(record, ensure_ascii=False, default=json_default) + "\n")
    return target


def log_event(event: str, payload: dict[str, Any] | None = None, config: HarnessConfig | None = None) -> Path:
    cfg = config or load_config()
    return append_jsonl(
        cfg.logs_dir / "events.jsonl",
        {
            "timestamp": utc_timestamp(),
            "event": event,
            "payload": payload or {},
        },
    )
