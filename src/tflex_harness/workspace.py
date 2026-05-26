from __future__ import annotations

import re
from typing import Any

from .artifacts import ArtifactStore
from .config import HarnessConfig, load_config

_SAFE_NAME_RE = re.compile(r"^[a-z][a-z0-9_]{0,63}$")


def validate_workspace_name(name: str) -> str:
    normalized = name.strip()
    if not _SAFE_NAME_RE.match(normalized):
        raise ValueError("name must match ^[a-z][a-z0-9_]{0,63}$")
    return normalized


def save_snippet_candidate(
    name: str,
    code: str,
    markdown: str | None = None,
    metadata: dict[str, Any] | None = None,
    config: HarnessConfig | None = None,
) -> dict[str, Any]:
    cfg = config or load_config()
    safe_name = validate_workspace_name(name)
    if not code.strip():
        raise ValueError("code must not be empty")

    target_dir = cfg.repo_dir / "agent_workspace" / "snippets" / safe_name
    target_dir.mkdir(parents=True, exist_ok=True)

    source_path = target_dir / "candidate.cs"
    markdown_path = target_dir / "README.md"
    metadata_path = target_dir / "metadata.json"

    source_path.write_text(code.rstrip() + "\n", encoding="utf-8")
    markdown_path.write_text((markdown or _default_candidate_markdown(safe_name)).rstrip() + "\n", encoding="utf-8")
    ArtifactStore(cfg).write_json(
        metadata_path,
        {
            "name": safe_name,
            "status": "candidate",
            "promotion_rule": "Promote to agent_workspace/recipes only after docs evidence, compile diagnostics, live run evidence, and documented assumptions/limitations.",
            "metadata": metadata or {},
        },
    )

    return {
        "ok": True,
        "name": safe_name,
        "status": "candidate",
        "directory": str(target_dir),
        "source_path": str(source_path),
        "markdown_path": str(markdown_path),
        "metadata_path": str(metadata_path),
    }


def _default_candidate_markdown(name: str) -> str:
    return f"""# {name}

Status: candidate, not verified.

Promotion checklist:

1. Add docs evidence from `dwnmf/tflex_api` or local docs via `TFLEX_API_DOCS_DIR`.
2. Compile through `run_csharp_tflex` and capture diagnostics.
3. Run live against T-FLEX CAD when available.
4. Record stdout/stderr, artifacts, blockers, assumptions, and limitations.
5. Move to `agent_workspace/recipes` only after repeated success.
"""
