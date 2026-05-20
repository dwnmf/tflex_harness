from __future__ import annotations

from pathlib import Path
from typing import Any

from .artifacts import ArtifactStore
from .config import HarnessConfig, load_config
from .runner import run_csharp_snippet


def list_recipes() -> list[dict[str, Any]]:
    return [
        {
            "name": "environment_probe",
            "description": "Initialize and exit a read-only minimal T-FLEX API session.",
            "args": {},
            "verified": True,
        },
        {
            "name": "create_empty_document",
            "description": "Create an invisible empty 2D document, save it as .grb, close it, and exit session.",
            "args": {"output_file": "optional absolute .grb path"},
            "verified": True,
        },
        {
            "name": "save_document_as_temp",
            "description": "Create a hidden 2D document and verify SaveAs to a temporary .grb artifact path.",
            "args": {"output_file": "optional absolute .grb path"},
            "verified": True,
        },
        {
            "name": "create_simple_2d_line",
            "description": "Create an invisible 2D document with two free nodes and a construction line through them.",
            "args": {"output_file": "optional absolute .grb path"},
            "verified": True,
        },
        {
            "name": "create_simple_3d_extrusion",
            "description": "Create an invisible 3D document with a circular profile and verified thicken extrusion.",
            "args": {"output_file": "optional absolute .grb path"},
            "verified": True,
        },
    ]


def _recipe_source(name: str, cfg: HarnessConfig) -> str:
    if name == "environment_probe":
        return (cfg.repo_dir / "agent_workspace" / "recipes" / "environment_probe.cs").read_text(encoding="utf-8")
    if name == "create_empty_document":
        return (cfg.repo_dir / "agent_workspace" / "recipes" / "create_empty_document.cs").read_text(encoding="utf-8")
    if name == "save_document_as_temp":
        return (cfg.repo_dir / "agent_workspace" / "recipes" / "save_document_as_temp.cs").read_text(encoding="utf-8")
    if name == "create_simple_2d_line":
        return (cfg.repo_dir / "agent_workspace" / "recipes" / "create_simple_2d_line.cs").read_text(encoding="utf-8")
    if name == "create_simple_3d_extrusion":
        return (cfg.repo_dir / "agent_workspace" / "recipes" / "create_simple_3d_extrusion.cs").read_text(encoding="utf-8")
    raise KeyError(f"Unknown recipe: {name}")


def run_recipe(name: str, args: dict[str, Any] | None = None, timeout_sec: int = 60, config: HarnessConfig | None = None) -> dict[str, Any]:
    cfg = config or load_config()
    args = dict(args or {})
    env: dict[str, str] = {}
    artifacts: dict[str, Any] = {}

    if name in {"create_empty_document", "save_document_as_temp", "create_simple_2d_line", "create_simple_3d_extrusion"}:
        output = args.get("output_file")
        if output:
            output_file = Path(str(output)).resolve()
            output_file.parent.mkdir(parents=True, exist_ok=True)
        else:
            doc_dir = ArtifactStore(cfg).create_tflex_doc_dir(f"recipe_{name}")
            output_name = {
                "create_empty_document": "empty_document.grb",
                "save_document_as_temp": "saved_document_as_temp.grb",
                "create_simple_2d_line": "simple_2d_line.grb",
                "create_simple_3d_extrusion": "simple_3d_extrusion.grb",
            }[name]
            output_file = doc_dir / output_name
        env["TFLEX_RECIPE_OUTPUT_FILE"] = str(output_file)
        artifacts["output_file"] = str(output_file)
    elif name != "environment_probe":
        raise KeyError(f"Unknown recipe: {name}")

    code = _recipe_source(name, cfg)
    result = run_csharp_snippet(
        code,
        mode="run",
        timeout_sec=timeout_sec,
        artifact_prefix=f"recipe_{name}",
        environment=env,
        config=cfg,
    )
    result["recipe"] = name
    result["recipe_args"] = args
    result["recipe_artifacts"] = artifacts
    return result
