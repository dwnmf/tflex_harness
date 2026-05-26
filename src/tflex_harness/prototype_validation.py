from __future__ import annotations

import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

from .artifacts import ArtifactStore, json_default
from .prototypes import scan_prototypes
from .recipes import run_recipe


RecipeRunner = Callable[[str, dict[str, Any], int], dict[str, Any]]


def validate_open_copy_save_batch(
    root: str | Path | None = None,
    *,
    category: str | None = None,
    limit: int | None = None,
    timeout_sec: int = 120,
    fail_fast: bool = False,
    dry_run: bool = False,
    output_dir: str | Path | None = None,
    recipe_runner: RecipeRunner | None = None,
) -> dict[str, Any]:
    catalog = scan_prototypes(root)
    prototypes = [item for item in catalog["files"] if item["extension"] == ".grb"]
    if category:
        prototypes = [item for item in prototypes if item["category"] == category]
    if limit is not None:
        prototypes = prototypes[:limit]

    out = _output_dir(output_dir)
    rows: list[dict[str, Any]] = []
    runner = recipe_runner or _run_recipe_adapter

    for index, proto in enumerate(prototypes, start=1):
        row = _base_row(index, proto, dry_run=dry_run)
        if dry_run:
            row.update({
                "status": "dry_run",
                "ok": True,
                "opened": None,
                "saved": None,
                "closed": None,
            })
            rows.append(row)
            continue

        result = runner("prototype_open_copy_save", {"source_path": proto["path"]}, timeout_sec)
        row.update(_result_to_row(result))
        rows.append(row)
        if fail_fast and not row["ok"]:
            break

    summary = _summary(catalog, prototypes, rows, root=Path(catalog["root"]), category=category, dry_run=dry_run)
    matrix = {
        "ok": summary["failed"] == 0,
        "summary": summary,
        "rows": rows,
    }
    matrix_path = out / "prototype_open_save_matrix.json"
    csv_path = out / "prototype_open_save_matrix.csv"
    matrix_path.write_text(json.dumps(matrix, ensure_ascii=False, indent=2, default=json_default) + "\n", encoding="utf-8")
    _write_csv(csv_path, rows)
    matrix["matrix_path"] = str(matrix_path)
    matrix["csv_path"] = str(csv_path)
    return matrix


def validate_title_mutation_batch(
    root: str | Path | None = None,
    *,
    category: str | None = None,
    limit: int | None = None,
    timeout_sec: int = 120,
    fail_fast: bool = False,
    dry_run: bool = False,
    output_dir: str | Path | None = None,
    property_name: str = "Title",
    value_prefix: str = "Harness Title Matrix",
    recipe_runner: RecipeRunner | None = None,
) -> dict[str, Any]:
    catalog = scan_prototypes(root)
    prototypes = [item for item in catalog["files"] if item["extension"] == ".grb"]
    if category:
        prototypes = [item for item in prototypes if item["category"] == category]
    if limit is not None:
        prototypes = prototypes[:limit]

    out = _output_dir(output_dir)
    rows: list[dict[str, Any]] = []
    runner = recipe_runner or _run_recipe_adapter

    for index, proto in enumerate(prototypes, start=1):
        text_value = f"{value_prefix} {index:03d}"
        row = _base_row(index, proto, dry_run=dry_run)
        row["property_name"] = property_name
        row["text_value"] = text_value
        if dry_run:
            row.update({
                "status": "dry_run",
                "ok": True,
                "opened": None,
                "saved": None,
                "closed": None,
                "property_persisted": None,
            })
            rows.append(row)
            continue

        result = runner(
            "prototype_set_document_property",
            {"source_path": proto["path"], "property_name": property_name, "text_value": text_value},
            timeout_sec,
        )
        row.update(_title_result_to_row(result, property_name=property_name, text_value=text_value))
        rows.append(row)
        if fail_fast and not row["ok"]:
            break

    summary = _summary(catalog, prototypes, rows, root=Path(catalog["root"]), category=category, dry_run=dry_run)
    summary["property_name"] = property_name
    summary["value_prefix"] = value_prefix
    summary["persisted"] = len([row for row in rows if row.get("property_persisted")])
    matrix = {
        "ok": summary["failed"] == 0,
        "summary": summary,
        "rows": rows,
    }
    matrix_path = out / "prototype_title_mutation_matrix.json"
    csv_path = out / "prototype_title_mutation_matrix.csv"
    matrix_path.write_text(json.dumps(matrix, ensure_ascii=False, indent=2, default=json_default) + "\n", encoding="utf-8")
    _write_csv(csv_path, rows)
    matrix["matrix_path"] = str(matrix_path)
    matrix["csv_path"] = str(csv_path)
    return matrix


def validate_table_cell_batch(
    root: str | Path | None = None,
    *,
    category: str | None = None,
    limit: int | None = None,
    timeout_sec: int = 120,
    fail_fast: bool = False,
    dry_run: bool = False,
    output_dir: str | Path | None = None,
    cell_index: int = 2,
    value_prefix: str = "Harness Table Matrix",
    recipe_runner: RecipeRunner | None = None,
) -> dict[str, Any]:
    catalog = scan_prototypes(root)
    prototypes = [item for item in catalog["files"] if item["extension"] == ".grb"]
    if category:
        prototypes = [item for item in prototypes if item["category"] == category]
    if limit is not None:
        prototypes = prototypes[:limit]

    out = _output_dir(output_dir)
    rows: list[dict[str, Any]] = []
    runner = recipe_runner or _run_recipe_adapter

    for index, proto in enumerate(prototypes, start=1):
        text_value = f"{value_prefix} {index:03d}"
        row = _base_row(index, proto, dry_run=dry_run)
        row["cell_index"] = cell_index
        row["text_value"] = text_value
        if dry_run:
            row.update({"status": "dry_run", "ok": True, "table_cell_persisted": None})
            rows.append(row)
            continue

        result = runner(
            "prototype_set_table_cell",
            {"source_path": proto["path"], "cell_index": str(cell_index), "text_value": text_value},
            timeout_sec,
        )
        row.update(_table_result_to_row(result, text_value=text_value))
        rows.append(row)
        if fail_fast and not row["ok"]:
            break

    summary = _summary(catalog, prototypes, rows, root=Path(catalog["root"]), category=category, dry_run=dry_run)
    summary["cell_index"] = cell_index
    summary["value_prefix"] = value_prefix
    summary["persisted"] = len([row for row in rows if row.get("table_cell_persisted")])
    matrix = {"ok": summary["failed"] == 0, "summary": summary, "rows": rows}
    matrix_path = out / "prototype_table_cell_matrix.json"
    csv_path = out / "prototype_table_cell_matrix.csv"
    matrix_path.write_text(json.dumps(matrix, ensure_ascii=False, indent=2, default=json_default) + "\n", encoding="utf-8")
    _write_csv(csv_path, rows)
    matrix["matrix_path"] = str(matrix_path)
    matrix["csv_path"] = str(csv_path)
    return matrix


def validate_first_visible_text_batch(
    root: str | Path | None = None,
    *,
    category: str | None = None,
    limit: int | None = None,
    timeout_sec: int = 120,
    fail_fast: bool = False,
    dry_run: bool = False,
    output_dir: str | Path | None = None,
    value_prefix: str = "Harness Visible Text Matrix",
    recipe_runner: RecipeRunner | None = None,
) -> dict[str, Any]:
    catalog = scan_prototypes(root)
    prototypes = [item for item in catalog["files"] if item["extension"] == ".grb"]
    if category:
        prototypes = [item for item in prototypes if item["category"] == category]
    if limit is not None:
        prototypes = prototypes[:limit]

    out = _output_dir(output_dir)
    rows: list[dict[str, Any]] = []
    runner = recipe_runner or _run_recipe_adapter

    for index, proto in enumerate(prototypes, start=1):
        text_value = f"{value_prefix} {index:03d}"
        row = _base_row(index, proto, dry_run=dry_run)
        row["text_value"] = text_value
        if dry_run:
            row.update({"status": "dry_run", "ok": True, "visible_text_persisted": None})
            rows.append(row)
            continue

        result = runner("prototype_replace_first_visible_text", {"source_path": proto["path"], "text_value": text_value}, timeout_sec)
        row.update(_first_visible_text_result_to_row(result, text_value=text_value))
        rows.append(row)
        if fail_fast and not row["ok"]:
            break

    summary = _summary(catalog, prototypes, rows, root=Path(catalog["root"]), category=category, dry_run=dry_run)
    summary["value_prefix"] = value_prefix
    summary["persisted"] = len([row for row in rows if row.get("visible_text_persisted")])
    matrix = {"ok": summary["failed"] == 0, "summary": summary, "rows": rows}
    matrix_path = out / "prototype_first_visible_text_matrix.json"
    csv_path = out / "prototype_first_visible_text_matrix.csv"
    matrix_path.write_text(json.dumps(matrix, ensure_ascii=False, indent=2, default=json_default) + "\n", encoding="utf-8")
    _write_csv(csv_path, rows)
    matrix["matrix_path"] = str(matrix_path)
    matrix["csv_path"] = str(csv_path)
    return matrix


def validate_specification_bom_field_batch(
    root: str | Path | None = None,
    *,
    category: str | None = "Спецификации",
    limit: int | None = None,
    timeout_sec: int = 120,
    fail_fast: bool = False,
    dry_run: bool = False,
    output_dir: str | Path | None = None,
    standard_field: str = "Desc",
    add_record: bool = True,
    value_prefix: str = "Harness Spec BOM Matrix",
    recipe_runner: RecipeRunner | None = None,
) -> dict[str, Any]:
    catalog = scan_prototypes(root)
    prototypes = [item for item in catalog["files"] if item["extension"] == ".grb"]
    if category:
        prototypes = [item for item in prototypes if item["category"] == category]
    if limit is not None:
        prototypes = prototypes[:limit]

    out = _output_dir(output_dir)
    rows: list[dict[str, Any]] = []
    runner = recipe_runner or _run_recipe_adapter

    for index, proto in enumerate(prototypes, start=1):
        text_value = f"{value_prefix} {index:03d}"
        row = _base_row(index, proto, dry_run=dry_run)
        row["standard_field"] = standard_field
        row["add_record"] = add_record
        row["text_value"] = text_value
        if dry_run:
            row.update({"status": "dry_run", "ok": True, "spec_field_persisted": None, "spec_bucket": "dry_run"})
            rows.append(row)
            continue

        result = runner(
            "prototype_set_specification_bom_field",
            {
                "source_path": proto["path"],
                "standard_field": standard_field,
                "text_value": text_value,
                "add_record": "true" if add_record else "false",
            },
            timeout_sec,
        )
        row.update(_spec_bom_result_to_row(result, text_value=text_value))
        rows.append(row)
        if fail_fast and not row["ok"]:
            break

    summary = _summary(catalog, prototypes, rows, root=Path(catalog["root"]), category=category, dry_run=dry_run)
    summary["standard_field"] = standard_field
    summary["add_record"] = add_record
    summary["value_prefix"] = value_prefix
    summary["persisted"] = len([row for row in rows if row.get("spec_field_persisted")])
    buckets: dict[str, int] = {}
    for row in rows:
        bucket = str(row.get("spec_bucket") or "unknown")
        buckets[bucket] = buckets.get(bucket, 0) + 1
    summary["buckets"] = buckets
    matrix = {"ok": summary["failed"] == 0, "summary": summary, "rows": rows}
    matrix_path = out / "prototype_specification_bom_field_matrix.json"
    csv_path = out / "prototype_specification_bom_field_matrix.csv"
    matrix_path.write_text(json.dumps(matrix, ensure_ascii=False, indent=2, default=json_default) + "\n", encoding="utf-8")
    _write_csv(csv_path, rows)
    matrix["matrix_path"] = str(matrix_path)
    matrix["csv_path"] = str(csv_path)
    return matrix


def validate_electrical_labels_batch(
    root: str | Path | None = None,
    *,
    category: str | None = "Электротехника",
    limit: int | None = None,
    timeout_sec: int = 120,
    fail_fast: bool = False,
    dry_run: bool = False,
    output_dir: str | Path | None = None,
    variable_name: str = "$Наименование",
    value_prefix: str = "Harness Electrical Label Matrix",
    recipe_runner: RecipeRunner | None = None,
) -> dict[str, Any]:
    catalog = scan_prototypes(root)
    prototypes = [item for item in catalog["files"] if item["extension"] == ".grb"]
    if category:
        prototypes = [item for item in prototypes if item["category"] == category]
    if limit is not None:
        prototypes = prototypes[:limit]

    out = _output_dir(output_dir)
    rows: list[dict[str, Any]] = []
    runner = recipe_runner or _run_recipe_adapter

    for index, proto in enumerate(prototypes, start=1):
        text_value = f"{value_prefix} {index:03d}"
        row = _base_row(index, proto, dry_run=dry_run)
        row["text_value"] = text_value
        row["variable_name"] = variable_name
        if dry_run:
            row.update({"status": "dry_run", "ok": True, "electrical_bucket": "dry_run"})
            rows.append(row)
            continue

        visible_result = runner(
            "prototype_replace_first_visible_text",
            {"source_path": proto["path"], "text_value": text_value},
            timeout_sec,
        )
        visible_row = _first_visible_text_result_to_row(visible_result, text_value=text_value)
        row.update(_prefixed_result_row(visible_row, "visible"))

        if visible_row.get("visible_text_persisted"):
            row.update({
                "status": "passed",
                "ok": True,
                "run_dir": visible_row.get("run_dir"),
                "copy_artifact": visible_row.get("copy_artifact"),
                "output_artifact": visible_row.get("output_artifact"),
                "electrical_bucket": "visible_text_supported",
                "electrical_persisted": True,
            })
            rows.append(row)
            continue

        variable_result = runner(
            "prototype_set_text_variable",
            {"source_path": proto["path"], "variable_name": variable_name, "text_value": text_value},
            timeout_sec,
        )
        variable_row = _text_variable_result_to_row(variable_result, variable_name=variable_name, text_value=text_value)
        row.update(_prefixed_result_row(variable_row, "variable"))
        row["run_dir"] = variable_row.get("run_dir") or visible_row.get("run_dir")
        row["copy_artifact"] = variable_row.get("copy_artifact") or visible_row.get("copy_artifact")
        row["output_artifact"] = variable_row.get("output_artifact") or visible_row.get("output_artifact")

        if variable_row.get("text_variable_persisted"):
            row["electrical_bucket"] = "variable_backed_supported"
            row["electrical_persisted"] = True
            row["ok"] = True
            row["status"] = "passed"
        elif not variable_row.get("text_variable_exists"):
            row["electrical_bucket"] = "unsupported_unknown"
            row["electrical_persisted"] = False
            row["ok"] = False
            row["status"] = "failed"
        else:
            row["electrical_bucket"] = "symbol_property_backed"
            row["electrical_persisted"] = False
            row["ok"] = False
            row["status"] = "failed"

        rows.append(row)
        if fail_fast and not row["ok"]:
            break

    summary = _summary(catalog, prototypes, rows, root=Path(catalog["root"]), category=category, dry_run=dry_run)
    summary["variable_name"] = variable_name
    summary["value_prefix"] = value_prefix
    summary["persisted"] = len([row for row in rows if row.get("electrical_persisted")])
    buckets: dict[str, int] = {}
    for row in rows:
        bucket = str(row.get("electrical_bucket") or "unsupported_unknown")
        buckets[bucket] = buckets.get(bucket, 0) + 1
    summary["buckets"] = buckets
    matrix = {"ok": summary["failed"] == 0, "summary": summary, "rows": rows}
    matrix_path = out / "prototype_electrical_labels_matrix.json"
    csv_path = out / "prototype_electrical_labels_matrix.csv"
    matrix_path.write_text(json.dumps(matrix, ensure_ascii=False, indent=2, default=json_default) + "\n", encoding="utf-8")
    _write_csv(csv_path, rows)
    matrix["matrix_path"] = str(matrix_path)
    matrix["csv_path"] = str(csv_path)
    return matrix


def _run_recipe_adapter(name: str, args: dict[str, Any], timeout_sec: int) -> dict[str, Any]:
    return run_recipe(name, args=args, timeout_sec=timeout_sec)


def _output_dir(output_dir: str | Path | None) -> Path:
    if output_dir is not None:
        out = Path(output_dir)
    else:
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        out = ArtifactStore().root / "prototype_validation" / stamp
    out.mkdir(parents=True, exist_ok=True)
    return out


def _base_row(index: int, proto: dict[str, Any], *, dry_run: bool) -> dict[str, Any]:
    return {
        "index": index,
        "id": proto["id"],
        "category": proto["category"],
        "relative_path": proto["relative_path"],
        "source_path": proto["path"],
        "source_size": proto["size"],
        "source_sha256": proto["sha256"],
        "dry_run": dry_run,
    }


def _result_to_row(result: dict[str, Any]) -> dict[str, Any]:
    stdout = str(result.get("stdout") or "")
    artifacts = result.get("artifacts") or []
    saved_artifact = _first_artifact_named(artifacts, "prototype_saved.grb")
    copy_artifact = _first_artifact_named(artifacts, "prototype_copy.grb")
    return {
        "status": "passed" if result.get("ok") else "failed",
        "ok": bool(result.get("ok")),
        "exit_code": result.get("exit_code"),
        "run_dir": result.get("run_dir"),
        "opened": "document.opened=True" in stdout,
        "saved": "document.saved=True" in stdout,
        "closed": "document.closed=True" in stdout,
        "session_closed": "easy.session=False" in stdout,
        "copy_artifact": copy_artifact.get("path") if copy_artifact else None,
        "copy_size": copy_artifact.get("size") if copy_artifact else None,
        "output_artifact": saved_artifact.get("path") if saved_artifact else None,
        "output_size": saved_artifact.get("size") if saved_artifact else None,
        "error": result.get("error"),
        "stage": result.get("stage"),
        "phase": result.get("phase"),
    }


def _title_result_to_row(result: dict[str, Any], *, property_name: str, text_value: str) -> dict[str, Any]:
    row = _result_to_row(result)
    stdout = str(result.get("stdout") or "")
    artifacts = result.get("artifacts") or []
    saved_artifact = _first_artifact_named(artifacts, "document_property_mutation_saved.grb")
    copy_artifact = _first_artifact_named(artifacts, "document_property_mutation_copy.grb")
    if copy_artifact:
        row["copy_artifact"] = copy_artifact.get("path")
        row["copy_size"] = copy_artifact.get("size")
    if saved_artifact:
        row["output_artifact"] = saved_artifact.get("path")
        row["output_size"] = saved_artifact.get("size")
    row["property_persisted"] = "documentProperty.persisted=True" in stdout
    row["property_after"] = f"documentProperty.after.{property_name}={text_value}" in stdout
    row["property_reopened"] = f"documentProperty.reopened={text_value}" in stdout
    row["ok"] = bool(row["ok"] and row["property_persisted"])
    row["status"] = "passed" if row["ok"] else "failed"
    return row


def _table_result_to_row(result: dict[str, Any], *, text_value: str) -> dict[str, Any]:
    row = _result_to_row(result)
    stdout = str(result.get("stdout") or "")
    row["table_cell_after"] = f"table.cell.after={text_value}" in stdout
    row["table_cell_reopened"] = f"table.cell.reopened={text_value}" in stdout
    row["table_cell_persisted"] = "table.cell.persisted=True" in stdout
    row["ok"] = bool(row["ok"] and row["table_cell_persisted"])
    row["status"] = "passed" if row["ok"] else "failed"
    return row


def _first_visible_text_result_to_row(result: dict[str, Any], *, text_value: str) -> dict[str, Any]:
    row = _result_to_row(result)
    stdout = str(result.get("stdout") or "")
    row["visible_text_after"] = f"firstVisibleText.after={text_value}" in stdout
    row["visible_text_reopened"] = f"firstVisibleText.reopened={text_value}" in stdout
    row["visible_text_persisted"] = "firstVisibleText.persisted=True" in stdout
    row["ok"] = bool(row["ok"] and row["visible_text_persisted"])
    row["status"] = "passed" if row["ok"] else "failed"
    return row


def _spec_bom_result_to_row(result: dict[str, Any], *, text_value: str) -> dict[str, Any]:
    row = _result_to_row(result)
    stdout = str(result.get("stdout") or "")
    saved_artifact = _first_artifact_named(result.get("artifacts") or [], "spec_field_mutation_saved.grb")
    copy_artifact = _first_artifact_named(result.get("artifacts") or [], "spec_field_mutation_copy.grb")
    if copy_artifact:
        row["copy_artifact"] = copy_artifact.get("path")
        row["copy_size"] = copy_artifact.get("size")
    if saved_artifact:
        row["output_artifact"] = saved_artifact.get("path")
        row["output_size"] = saved_artifact.get("size")
    row["spec_bom_exists"] = "spec.bom.exists=True" in stdout
    row["spec_record_added"] = "spec.record.added=True" in stdout
    row["spec_field_after"] = f"spec.field.after={text_value}" in stdout
    row["spec_field_reopened"] = f"spec.field.reopened={text_value}" in stdout
    row["spec_field_persisted"] = "spec.field.persisted=True" in stdout
    if row["spec_field_persisted"]:
        row["spec_bucket"] = "bom_standard_field_supported"
    elif not row["spec_bom_exists"]:
        row["spec_bucket"] = "no_bom_object"
    elif "spec.error=" in stdout:
        row["spec_bucket"] = "bom_api_error"
    else:
        row["spec_bucket"] = "bom_no_persist"
    row["ok"] = bool(row["ok"] and row["spec_field_persisted"])
    row["status"] = "passed" if row["ok"] else "failed"
    return row


def _text_variable_result_to_row(result: dict[str, Any], *, variable_name: str, text_value: str) -> dict[str, Any]:
    row = _result_to_row(result)
    stdout = str(result.get("stdout") or "")
    saved_artifact = _first_artifact_named(result.get("artifacts") or [], "variable_mutation_saved.grb")
    copy_artifact = _first_artifact_named(result.get("artifacts") or [], "variable_mutation_copy.grb")
    if copy_artifact:
        row["copy_artifact"] = copy_artifact.get("path")
        row["copy_size"] = copy_artifact.get("size")
    if saved_artifact:
        row["output_artifact"] = saved_artifact.get("path")
        row["output_size"] = saved_artifact.get("size")
    row["text_variable_name"] = variable_name
    row["text_variable_exists"] = "variable.exists=True" in stdout
    row["text_variable_set"] = "variable.set=True" in stdout
    row["text_variable_reopened"] = f"variable.reopened={text_value}" in stdout
    row["text_variable_persisted"] = "variable.persisted=True" in stdout
    row["ok"] = bool(row["ok"] and row["text_variable_persisted"])
    row["status"] = "passed" if row["ok"] else "failed"
    return row


def _prefixed_result_row(row: dict[str, Any], prefix: str) -> dict[str, Any]:
    keep = {
        "status",
        "ok",
        "exit_code",
        "run_dir",
        "opened",
        "saved",
        "closed",
        "session_closed",
        "copy_artifact",
        "copy_size",
        "output_artifact",
        "output_size",
        "error",
        "stage",
        "phase",
        "visible_text_after",
        "visible_text_reopened",
        "visible_text_persisted",
        "text_variable_name",
        "text_variable_exists",
        "text_variable_set",
        "text_variable_reopened",
        "text_variable_persisted",
    }
    return {f"{prefix}_{key}": value for key, value in row.items() if key in keep}


def _first_artifact_named(artifacts: list[dict[str, Any]], name: str) -> dict[str, Any] | None:
    for artifact in artifacts:
        if str(artifact.get("relative_path", "")).endswith(name) or str(artifact.get("path", "")).endswith(name):
            return artifact
    return None


def _summary(
    catalog: dict[str, Any],
    prototypes: list[dict[str, Any]],
    rows: list[dict[str, Any]],
    *,
    root: Path,
    category: str | None,
    dry_run: bool,
) -> dict[str, Any]:
    attempted = len(rows)
    passed = len([row for row in rows if row.get("ok")])
    failed = attempted - passed
    return {
        "root": str(root),
        "category": category,
        "dry_run": dry_run,
        "catalog_grb_count": catalog["grb_count"],
        "selected": len(prototypes),
        "attempted": attempted,
        "passed": passed,
        "failed": failed,
    }


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    fieldnames = [
        "index",
        "id",
        "category",
        "relative_path",
        "status",
        "ok",
        "opened",
        "saved",
        "closed",
        "session_closed",
        "property_name",
        "text_value",
        "property_after",
        "property_reopened",
        "property_persisted",
        "cell_index",
        "table_cell_after",
        "table_cell_reopened",
        "table_cell_persisted",
        "visible_text_after",
        "visible_text_reopened",
        "visible_text_persisted",
        "variable_name",
        "visible_ok",
        "visible_run_dir",
        "variable_ok",
        "variable_run_dir",
        "variable_text_variable_exists",
        "variable_text_variable_set",
        "variable_text_variable_reopened",
        "variable_text_variable_persisted",
        "electrical_bucket",
        "electrical_persisted",
        "standard_field",
        "add_record",
        "spec_bom_exists",
        "spec_record_added",
        "spec_field_after",
        "spec_field_reopened",
        "spec_field_persisted",
        "spec_bucket",
        "source_size",
        "copy_size",
        "output_size",
        "run_dir",
        "source_path",
        "copy_artifact",
        "output_artifact",
        "error",
    ]
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
