from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from .artifacts import ArtifactStore
from .config import HarnessConfig, load_config
from .prototypes import find_prototype
from .runner import run_csharp_snippet

_REQUIRED_EVIDENCE_PHRASES = (
    "## Live Verification Report",
    "Test:",
    "Docs used:",
    "Snippet:",
    "Result:",
    "Evidence:",
    "Blockers:",
)

_FALLBACK_RECIPE_DEFINITIONS: tuple[dict[str, Any], ...] = (
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


def _sha256(path: Path) -> str | None:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError:
        return None


def _recipe_paths(name: str, cfg: HarnessConfig) -> dict[str, str]:
    recipes_dir = cfg.repo_dir / "agent_workspace" / "recipes"
    return {
        "source_path": str(recipes_dir / f"{name}.cs"),
        "markdown_path": str(recipes_dir / f"{name}.md"),
        "metadata_path": str(recipes_dir / f"{name}.recipe.json"),
    }


class RecipeRegistry:
    def __init__(self, config: HarnessConfig | None = None) -> None:
        self.config = config or load_config()
        self.recipes_dir = self.config.repo_dir / "agent_workspace" / "recipes"

    def list(self) -> list[dict[str, Any]]:
        discovered = {path.stem.removesuffix(".recipe") for path in self.recipes_dir.glob("*.recipe.json")}
        fallback = {str(recipe["name"]) for recipe in _FALLBACK_RECIPE_DEFINITIONS}
        return [self.definition(name) for name in sorted(discovered | fallback)]

    def known_names(self) -> list[str]:
        return [str(recipe["name"]) for recipe in self.list()]

    def definition(self, name: str) -> dict[str, Any]:
        paths = _recipe_paths(name, self.config)
        metadata_path = Path(paths["metadata_path"])
        if metadata_path.exists():
            data = json.loads(metadata_path.read_text(encoding="utf-8"))
            if data.get("name") != name:
                data["verified"] = False
                data["freshness"] = {"status": "stale", "reason": "metadata name mismatch"}
        else:
            data = self._fallback_definition(name)
            data["freshness"] = {"status": "fallback", "reason": "metadata missing"}
        data.update(paths)
        data["source_exists"] = Path(paths["source_path"]).exists()
        data["markdown_exists"] = Path(paths["markdown_path"]).exists()
        self._apply_freshness(data)
        return data

    @staticmethod
    def _fallback_definition(name: str) -> dict[str, Any]:
        for recipe in _FALLBACK_RECIPE_DEFINITIONS:
            if recipe["name"] == name:
                return dict(recipe)
        raise KeyError(f"Unknown recipe: {name}")

    def _apply_freshness(self, data: dict[str, Any]) -> None:
        source_path = Path(data["source_path"])
        markdown_path = Path(data["markdown_path"])
        source_hash = _sha256(source_path)
        markdown_hash = _sha256(markdown_path)
        stale_reasons: list[str] = []
        if source_hash != data.get("source_sha256"):
            stale_reasons.append("source hash mismatch")
        if markdown_hash != data.get("markdown_sha256"):
            stale_reasons.append("markdown hash mismatch")
        if data.get("verified") is True and markdown_path.exists():
            text = markdown_path.read_text(encoding="utf-8", errors="ignore")
            missing = [phrase for phrase in _REQUIRED_EVIDENCE_PHRASES if phrase not in text]
            stale_reasons.extend(f"missing evidence phrase: {phrase}" for phrase in missing)
        if stale_reasons:
            data["verified"] = False
            data["freshness"] = {"status": "stale", "reasons": stale_reasons}
        else:
            data["freshness"] = {"status": "fresh"}
        data["source_sha256_actual"] = source_hash
        data["markdown_sha256_actual"] = markdown_hash

    def source(self, name: str) -> str:
        self.definition(name)
        return Path(_recipe_paths(name, self.config)["source_path"]).read_text(encoding="utf-8")


def _recipe_definition(name: str, cfg: HarnessConfig | None = None) -> dict[str, Any]:
    return RecipeRegistry(cfg).definition(name)


def _known_recipe_names(config: HarnessConfig | None = None) -> list[str]:
    return RecipeRegistry(config).known_names()


def _output_root(cfg: HarnessConfig) -> Path:
    return (cfg.artifacts_dir / "tflex_docs").resolve()


def _is_under(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def list_recipes(config: HarnessConfig | None = None) -> list[dict[str, Any]]:
    return RecipeRegistry(config).list()


def _recipe_source(name: str, cfg: HarnessConfig) -> str:
    return RecipeRegistry(cfg).source(name)


def run_recipe(name: str, args: dict[str, Any] | None = None, timeout_sec: int = 60, config: HarnessConfig | None = None) -> dict[str, Any]:
    cfg = config or load_config()
    registry = RecipeRegistry(cfg)
    args = dict(args or {})
    env: dict[str, str] = {}
    artifacts: dict[str, Any] = {}

    known_names = registry.known_names()
    if name not in known_names:
        return {
            "ok": False,
            "stage": "input",
            "error": "unknown recipe",
            "recipe": name,
            "known_recipes": known_names,
            "recipe_args": args,
            "recipe_artifacts": {},
        }

    recipe_info = registry.definition(name)

    if name in {"create_empty_document", "save_document_as_temp", "create_simple_2d_line", "create_simple_3d_extrusion"}:
        output = args.get("output_file")
        if output:
            output_file = Path(str(output)).resolve()
            output_root = _output_root(cfg)
            if not _is_under(output_file, output_root):
                return {
                    "ok": False,
                    "stage": "input",
                    "error": "recipe output_file must be under artifacts/tflex_docs",
                    "recipe": name,
                    "recipe_args": args,
                    "allowed_output_root": str(output_root),
                    "recipe_artifacts": {},
                    "recipe_info": recipe_info,
                }
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

    if name == "prototype_open_copy_save":
        source_result = _resolve_prototype_source_arg(args, name, recipe_info)
        if source_result.get("ok") is False:
            return source_result
        source_path = Path(str(source_result["source_path"])).resolve()
        env["TFLEX_PROTOTYPE_SOURCE_PATH"] = str(source_path)
        artifacts["source_path"] = str(source_path)

    if name == "prototype_set_text_variable":
        source_result = _resolve_prototype_source_arg(args, name, recipe_info)
        if source_result.get("ok") is False:
            return source_result
        variable_name = args.get("variable_name")
        if not variable_name:
            return {
                "ok": False,
                "stage": "input",
                "error": "variable_name is required",
                "recipe": name,
                "recipe_args": args,
                "recipe_artifacts": {},
                "recipe_info": recipe_info,
            }
        source_path = Path(str(source_result["source_path"])).resolve()
        env["TFLEX_PROTOTYPE_SOURCE_PATH"] = str(source_path)
        env["TFLEX_VARIABLE_NAME"] = str(variable_name)
        env["TFLEX_VARIABLE_TEXT_VALUE"] = str(args.get("text_value") or "")
        artifacts["source_path"] = str(source_path)
        artifacts["variable_name"] = str(variable_name)

    code = registry.source(name)
    helpers = recipe_info.get("helpers")
    result = run_csharp_snippet(
        code,
        mode="run",
        timeout_sec=timeout_sec,
        artifact_prefix=f"recipe_{name}",
        environment=env,
        helpers=helpers if isinstance(helpers, list) else None,
        config=cfg,
    )
    result["recipe"] = name
    result["recipe_args"] = args
    result["recipe_artifacts"] = artifacts
    result["recipe_info"] = recipe_info
    return result


def _resolve_prototype_source_arg(args: dict[str, Any], recipe_name: str, recipe_info: dict[str, Any]) -> dict[str, Any]:
    source = args.get("source_path") or args.get("prototype_path")
    selector = args.get("prototype_id") or args.get("prototype_selector")
    if not source and selector:
        try:
            prototype = find_prototype(str(selector))
        except KeyError as exc:
            return {
                "ok": False,
                "stage": "input",
                "error": str(exc),
                "recipe": recipe_name,
                "recipe_args": args,
                "recipe_artifacts": {},
                "recipe_info": recipe_info,
            }
        source = prototype["path"]
    if not source:
        return {
            "ok": False,
            "stage": "input",
            "error": "source_path or prototype_id is required",
            "recipe": recipe_name,
            "recipe_args": args,
            "recipe_artifacts": {},
            "recipe_info": recipe_info,
        }
    source_path = Path(str(source)).resolve()
    if not source_path.exists():
        return {
            "ok": False,
            "stage": "input",
            "error": "source_path does not exist",
            "recipe": recipe_name,
            "source_path": str(source_path),
            "recipe_args": args,
            "recipe_artifacts": {},
            "recipe_info": recipe_info,
        }
    return {"ok": True, "source_path": str(source_path)}
