from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .artifacts import ArtifactStore, json_default
from .config import HarnessConfig, load_config
from .recipes import run_recipe


def create_document_from_payload(
    payload_path: str | Path,
    *,
    timeout_sec: int = 120,
    dry_run: bool = False,
    config: HarnessConfig | None = None,
    recipe_runner=run_recipe,
) -> dict[str, Any]:
    cfg = config or load_config()
    path = Path(payload_path).resolve()
    if not path.exists():
        return {"ok": False, "stage": "input", "error": "payload file does not exist", "payload_path": str(path)}

    try:
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as exc:
        return {"ok": False, "stage": "input", "error": "payload JSON is invalid", "payload_path": str(path), "detail": str(exc)}

    if not isinstance(payload, dict):
        return {"ok": False, "stage": "input", "error": "payload root must be an object", "payload_path": str(path)}

    plan = plan_document_creation(payload)
    store = ArtifactStore(cfg)
    factory_dir = store.create_run_dir("document_factory")
    input_copy = factory_dir / "input_payload.json"
    input_copy.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=json_default) + "\n", encoding="utf-8")
    plan_path = factory_dir / "factory_plan.json"

    result: dict[str, Any] = {
        "ok": plan["ok"] if dry_run else False,
        "stage": "dry_run" if dry_run else "run",
        "payload_path": str(path),
        "factory_run_dir": str(factory_dir),
        "input_payload_path": str(input_copy),
        "plan_path": str(plan_path),
        "plan": plan,
        "dry_run": dry_run,
    }
    plan_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2, default=json_default) + "\n", encoding="utf-8")

    if not plan["ok"]:
        result["ok"] = False
        result["stage"] = "input"
        return result
    if dry_run:
        return result

    recipe_result = recipe_runner(plan["recipe"], args=plan["recipe_args"], timeout_sec=timeout_sec, config=cfg)
    result["recipe_result"] = recipe_result
    result["ok"] = recipe_result.get("ok") is True
    result["stage"] = recipe_result.get("stage", "run")
    result["recipe"] = plan["recipe"]
    result["recipe_args"] = plan["recipe_args"]
    result["recipe_run_dir"] = recipe_result.get("run_dir")
    return result


def plan_document_creation(payload: dict[str, Any]) -> dict[str, Any]:
    prototype_args = _prototype_args(payload.get("prototype"))
    if prototype_args.get("ok") is False:
        return prototype_args

    explicit = payload.get("recipe")
    if isinstance(explicit, dict):
        recipe_name = explicit.get("name")
        recipe_args = dict(explicit.get("args") or {})
        if not recipe_name:
            return {"ok": False, "stage": "input", "error": "recipe.name is required"}
        recipe_args = {**prototype_args["args"], **recipe_args}
        return _plan(str(recipe_name), recipe_args, payload, selection="explicit_recipe")
    if isinstance(explicit, str) and explicit:
        return _plan(explicit, dict(prototype_args["args"]), payload, selection="explicit_recipe")

    document = payload.get("document") or {}
    if not isinstance(document, dict):
        return {"ok": False, "stage": "input", "error": "document must be an object"}

    properties = document.get("properties") or {}
    if isinstance(properties, dict) and properties:
        name, value = next(iter(properties.items()))
        args = {**prototype_args["args"], "property_name": str(name), "text_value": "" if value is None else str(value)}
        return _plan("prototype_set_document_property", args, payload, selection="document.properties")

    variables = document.get("variables") or {}
    if isinstance(variables, dict) and variables:
        name, value = next(iter(variables.items()))
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            args = {**prototype_args["args"], "variable_name": str(name), "real_value": str(value)}
            return _plan("prototype_set_real_variable", args, payload, selection="document.variables.real")
        args = {**prototype_args["args"], "variable_name": str(name), "text_value": "" if value is None else str(value)}
        return _plan("prototype_set_text_variable", args, payload, selection="document.variables.text")

    replacements = document.get("text_replacements") or {}
    if isinstance(replacements, dict) and replacements:
        search, replacement = next(iter(replacements.items()))
        args = {**prototype_args["args"], "search_text": str(search), "replacement_text": "" if replacement is None else str(replacement)}
        return _plan("prototype_replace_visible_text", args, payload, selection="document.text_replacements")

    tables = document.get("tables") or []
    if isinstance(tables, list) and tables:
        first = tables[0]
        if not isinstance(first, dict):
            return {"ok": False, "stage": "input", "error": "document.tables[0] must be an object"}
        if "cell_index" not in first:
            return {"ok": False, "stage": "input", "error": "document.tables[0].cell_index is required"}
        value = first.get("text_value", first.get("value", ""))
        args = {**prototype_args["args"], "cell_index": str(first["cell_index"]), "text_value": "" if value is None else str(value)}
        return _plan("prototype_set_table_cell", args, payload, selection="document.tables")

    return _plan("prototype_open_copy_save", dict(prototype_args["args"]), payload, selection="open_copy_save")


def _prototype_args(prototype: Any) -> dict[str, Any]:
    if not isinstance(prototype, dict):
        return {"ok": False, "stage": "input", "error": "prototype object is required"}
    args: dict[str, str] = {}
    if prototype.get("path"):
        args["source_path"] = str(prototype["path"])
    elif prototype.get("id"):
        args["prototype_id"] = str(prototype["id"])
    elif prototype.get("selector"):
        args["prototype_selector"] = str(prototype["selector"])
    else:
        return {"ok": False, "stage": "input", "error": "prototype.id, prototype.path, or prototype.selector is required"}
    return {"ok": True, "args": args}


def _plan(recipe: str, args: dict[str, str], payload: dict[str, Any], *, selection: str) -> dict[str, Any]:
    pending = _pending_operations(payload, selection)
    return {
        "ok": True,
        "recipe": recipe,
        "recipe_args": args,
        "selection": selection,
        "limitations": [
            "Phase 6 factory currently dispatches one verified recipe per payload run.",
            "If payload contains multiple mutation groups, only the first supported group is executed and the rest are reported as pending_operations.",
        ],
        "pending_operations": pending,
    }


def _pending_operations(payload: dict[str, Any], selected: str) -> list[str]:
    document = payload.get("document") or {}
    if not isinstance(document, dict):
        return []
    groups = [
        ("document.properties", document.get("properties")),
        ("document.variables", document.get("variables")),
        ("document.text_replacements", document.get("text_replacements")),
        ("document.tables", document.get("tables")),
    ]
    pending: list[str] = []
    for name, value in groups:
        if name == selected or selected.startswith(name + "."):
            continue
        if isinstance(value, dict) and value:
            pending.append(name)
        elif isinstance(value, list) and value:
            pending.append(name)
    return pending
