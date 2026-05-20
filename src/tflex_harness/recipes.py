from __future__ import annotations

from pathlib import Path
from typing import Any

from .artifacts import ArtifactStore
from .config import HarnessConfig, load_config
from .runner import run_csharp_snippet

_RECIPE_DEFINITIONS: tuple[dict[str, Any], ...] = (
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
)


def _recipe_paths(name: str, cfg: HarnessConfig) -> dict[str, str]:
    recipes_dir = cfg.repo_dir / "agent_workspace" / "recipes"
    return {
        "source_path": str(recipes_dir / f"{name}.cs"),
        "markdown_path": str(recipes_dir / f"{name}.md"),
    }


def _recipe_definition(name: str) -> dict[str, Any]:
    for recipe in _RECIPE_DEFINITIONS:
        if recipe["name"] == name:
            return dict(recipe)
    raise KeyError(f"Unknown recipe: {name}")


def _known_recipe_names() -> list[str]:
    return [str(recipe["name"]) for recipe in _RECIPE_DEFINITIONS]


def list_recipes(config: HarnessConfig | None = None) -> list[dict[str, Any]]:
    cfg = config or load_config()
    recipes: list[dict[str, Any]] = []
    for definition in _RECIPE_DEFINITIONS:
        recipe = dict(definition)
        recipe.update(_recipe_paths(recipe["name"], cfg))
        recipe["source_exists"] = Path(recipe["source_path"]).exists()
        recipe["markdown_exists"] = Path(recipe["markdown_path"]).exists()
        recipes.append(recipe)
    return recipes


def _recipe_source(name: str, cfg: HarnessConfig) -> str:
    _recipe_definition(name)
    return Path(_recipe_paths(name, cfg)["source_path"]).read_text(encoding="utf-8")


def run_recipe(name: str, args: dict[str, Any] | None = None, timeout_sec: int = 60, config: HarnessConfig | None = None) -> dict[str, Any]:
    cfg = config or load_config()
    args = dict(args or {})
    env: dict[str, str] = {}
    artifacts: dict[str, Any] = {}

    if name not in _known_recipe_names():
        return {
            "ok": False,
            "stage": "input",
            "error": "unknown recipe",
            "recipe": name,
            "known_recipes": _known_recipe_names(),
            "recipe_args": args,
            "recipe_artifacts": {},
        }

    recipe_info = _recipe_definition(name)
    recipe_info.update(_recipe_paths(name, cfg))
    recipe_info["source_exists"] = Path(recipe_info["source_path"]).exists()
    recipe_info["markdown_exists"] = Path(recipe_info["markdown_path"]).exists()

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
    result["recipe_info"] = recipe_info
    return result
