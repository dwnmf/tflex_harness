from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

from .artifacts import ArtifactStore, json_default
from .document_factory import create_document_from_payload, plan_document_creation
from .prototype_metadata import capture_prototype_metadata
from .prototypes import find_prototype


FactoryRunner = Callable[[Path, int, bool], dict[str, Any]]
MetadataCapture = Callable[[dict[str, Any], int], dict[str, Any]]


def create_documents_from_payload_dir(
    payload_dir: str | Path | None = None,
    *,
    pattern: str = "*.json",
    recursive: bool = False,
    failed_matrix: str | Path | None = None,
    audit_open_only: bool = False,
    timeout_sec: int = 120,
    dry_run: bool = False,
    fail_fast: bool = False,
    output_dir: str | Path | None = None,
    factory_runner: FactoryRunner | None = None,
    metadata_capture: MetadataCapture | None = None,
) -> dict[str, Any]:
    if not pattern:
        return {"ok": False, "stage": "input", "error": "pattern is required", "payload_dir": str(Path(payload_dir).resolve()) if payload_dir else None}
    selection = _select_payloads(payload_dir, pattern=pattern, recursive=recursive, failed_matrix=failed_matrix)
    if selection.get("ok") is False:
        return selection

    payloads = selection["payloads"]
    out = _output_dir(output_dir)
    runner = factory_runner or _factory_runner_adapter
    audit_capture = metadata_capture or capture_prototype_metadata
    rows: list[dict[str, Any]] = []

    for index, payload_path in enumerate(payloads, start=1):
        if audit_open_only:
            result = _open_only_audit_payload(payload_path, timeout_sec=timeout_sec, dry_run=dry_run, metadata_capture=audit_capture)
        else:
            result = runner(payload_path, timeout_sec, dry_run)
        row = _row_from_result(index, payload_path, result, dry_run=dry_run)
        rows.append(row)
        if fail_fast and not row["ok"]:
            break

    summary = _summary(rows, selected=len(payloads), dry_run=dry_run)
    matrix = {
        "ok": summary["failed"] == 0,
        "stage": "dry_run" if dry_run else "run",
        "payload_dir": selection.get("payload_dir"),
        "failed_matrix": selection.get("failed_matrix"),
        "selection": selection["selection"],
        "audit_open_only": audit_open_only,
        "pattern": pattern,
        "recursive": recursive,
        "summary": summary,
        "rows": rows,
    }
    matrix_path = out / "document_factory_batch_matrix.json"
    csv_path = out / "document_factory_batch_matrix.csv"
    failure_report = _failure_report(matrix)
    failure_report_path = out / "document_factory_failure_report.json"
    matrix_path.write_text(json.dumps(matrix, ensure_ascii=False, indent=2, default=json_default) + "\n", encoding="utf-8")
    failure_report_path.write_text(json.dumps(failure_report, ensure_ascii=False, indent=2, default=json_default) + "\n", encoding="utf-8")
    _write_csv(csv_path, rows)
    matrix["matrix_path"] = str(matrix_path)
    matrix["csv_path"] = str(csv_path)
    matrix["failure_report_path"] = str(failure_report_path)
    return matrix


def _factory_runner_adapter(payload_path: Path, timeout_sec: int, dry_run: bool) -> dict[str, Any]:
    return create_document_from_payload(payload_path, timeout_sec=timeout_sec, dry_run=dry_run)


def _open_only_audit_payload(
    payload_path: Path,
    *,
    timeout_sec: int,
    dry_run: bool,
    metadata_capture: MetadataCapture,
) -> dict[str, Any]:
    if not payload_path.exists():
        return {"ok": False, "stage": "input", "error": "payload file does not exist", "payload_path": str(payload_path), "audit_open_only": True}
    try:
        payload = json.loads(payload_path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as exc:
        return {"ok": False, "stage": "input", "error": "payload JSON is invalid", "payload_path": str(payload_path), "detail": str(exc), "audit_open_only": True}
    if not isinstance(payload, dict):
        return {"ok": False, "stage": "input", "error": "payload root must be an object", "payload_path": str(payload_path), "audit_open_only": True}

    plan = plan_document_creation(payload)
    result: dict[str, Any] = {
        "ok": plan.get("ok") is True,
        "stage": "audit_dry_run" if dry_run else "audit",
        "payload_path": str(payload_path),
        "plan": plan,
        "dry_run": dry_run,
        "audit_open_only": True,
    }
    if plan.get("ok") is False:
        result["ok"] = False
        result["stage"] = "input"
        result["error"] = plan.get("error")
        return result
    prototype_result = _prototype_from_recipe_args(plan.get("recipe_args") or {})
    if prototype_result.get("ok") is False:
        result.update(prototype_result)
        result["stage"] = "input"
        result["ok"] = False
        return result
    result["prototype"] = prototype_result["prototype"]
    if dry_run:
        return result

    audit = metadata_capture(prototype_result["prototype"], timeout_sec)
    metadata = audit.get("metadata") if isinstance(audit.get("metadata"), dict) else {}
    run = audit.get("run") if isinstance(audit.get("run"), dict) else {}
    result["metadata"] = metadata
    result["audit_result"] = audit
    result["audit_run_dir"] = run.get("run_dir")
    result["factory_run_dir"] = run.get("run_dir")
    result["ok"] = audit.get("ok") is True
    if not result["ok"]:
        result["error"] = "open-only audit failed"
    return result


def _prototype_from_recipe_args(args: dict[str, Any]) -> dict[str, Any]:
    try:
        if args.get("source_path"):
            path = Path(str(args["source_path"])).resolve()
            if not path.exists():
                return {"ok": False, "error": "prototype source path does not exist", "source_path": str(path)}
            return {"ok": True, "prototype": _prototype_record_from_path(path)}
        selector = args.get("prototype_id") or args.get("prototype_selector")
        if selector:
            return {"ok": True, "prototype": find_prototype(str(selector), required=True)}
    except KeyError as exc:
        return {"ok": False, "error": str(exc)}
    return {"ok": False, "error": "prototype source could not be resolved from payload"}


def _prototype_record_from_path(path: Path) -> dict[str, Any]:
    data = path.read_bytes()
    return {
        "id": path.stem,
        "name": path.name,
        "category": "",
        "relative_path": path.name,
        "path": str(path),
        "extension": path.suffix.lower(),
        "size": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
    }


def _select_payloads(
    payload_dir: str | Path | None,
    *,
    pattern: str,
    recursive: bool,
    failed_matrix: str | Path | None,
) -> dict[str, Any]:
    if failed_matrix is not None:
        matrix_path = Path(failed_matrix).resolve()
        if not matrix_path.exists():
            return {"ok": False, "stage": "input", "error": "failed matrix does not exist", "failed_matrix": str(matrix_path)}
        try:
            matrix = json.loads(matrix_path.read_text(encoding="utf-8-sig"))
        except json.JSONDecodeError as exc:
            return {"ok": False, "stage": "input", "error": "failed matrix JSON is invalid", "failed_matrix": str(matrix_path), "detail": str(exc)}
        if not isinstance(matrix, dict) or not isinstance(matrix.get("rows"), list):
            return {"ok": False, "stage": "input", "error": "failed matrix must contain rows array", "failed_matrix": str(matrix_path)}
        payloads = []
        for row in matrix["rows"]:
            if not isinstance(row, dict) or row.get("ok") is True:
                continue
            payload = row.get("payload_path")
            if payload:
                payloads.append(Path(str(payload)).resolve())
        return {
            "ok": True,
            "selection": "failed_matrix",
            "payload_dir": None,
            "failed_matrix": str(matrix_path),
            "payloads": payloads,
        }

    if payload_dir is None:
        return {"ok": False, "stage": "input", "error": "payload directory or failed matrix is required", "payload_dir": None}
    source_dir = Path(payload_dir).resolve()
    if not source_dir.exists():
        return {"ok": False, "stage": "input", "error": "payload directory does not exist", "payload_dir": str(source_dir)}
    if not source_dir.is_dir():
        return {"ok": False, "stage": "input", "error": "payload path is not a directory", "payload_dir": str(source_dir)}
    return {
        "ok": True,
        "selection": "payload_dir",
        "payload_dir": str(source_dir),
        "failed_matrix": None,
        "payloads": _payload_paths(source_dir, pattern=pattern, recursive=recursive),
    }


def _payload_paths(source_dir: Path, *, pattern: str, recursive: bool) -> list[Path]:
    iterator = source_dir.rglob(pattern) if recursive else source_dir.glob(pattern)
    return sorted(path for path in iterator if path.is_file())


def _output_dir(output_dir: str | Path | None) -> Path:
    if output_dir is not None:
        out = Path(output_dir)
    else:
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        out = ArtifactStore().root / "document_factory_batches" / stamp
    out.mkdir(parents=True, exist_ok=True)
    return out


def _row_from_result(index: int, payload_path: Path, result: dict[str, Any], *, dry_run: bool) -> dict[str, Any]:
    plan = result.get("plan") if isinstance(result.get("plan"), dict) else {}
    recipe_result = result.get("recipe_result") if isinstance(result.get("recipe_result"), dict) else {}
    outputs = result.get("outputs") if isinstance(result.get("outputs"), list) else []
    first_output = outputs[0] if outputs else {}
    step_output = next((item for item in outputs if item.get("format") == "step"), {})
    pdf_output = next((item for item in outputs if item.get("format") == "pdf"), {})
    dxf_output = next((item for item in outputs if item.get("format") == "dxf"), {})
    dwg_output = next((item for item in outputs if item.get("format") == "dwg"), {})
    failure_kind = _failure_kind(result)
    metadata = result.get("metadata") if isinstance(result.get("metadata"), dict) else {}
    counts = metadata.get("counts") if isinstance(metadata.get("counts"), dict) else {}
    return {
        "index": index,
        "payload_name": payload_path.stem,
        "payload_path": str(payload_path),
        "status": "passed" if result.get("ok") else "failed",
        "ok": bool(result.get("ok")),
        "failure_kind": failure_kind,
        "dry_run": dry_run,
        "audit_open_only": bool(result.get("audit_open_only")),
        "stage": result.get("stage"),
        "factory_run_dir": result.get("factory_run_dir"),
        "audit_run_dir": result.get("audit_run_dir"),
        "recipe": result.get("recipe") or plan.get("recipe"),
        "selection": plan.get("selection"),
        "planned_output": plan.get("output"),
        "output_formats": [item.get("format") for item in outputs],
        "output_path": first_output.get("path"),
        "output_size": first_output.get("size"),
        "step_output_path": step_output.get("path"),
        "step_output_size": step_output.get("size"),
        "pdf_output_path": pdf_output.get("path"),
        "pdf_output_size": pdf_output.get("size"),
        "dxf_output_path": dxf_output.get("path"),
        "dxf_output_size": dxf_output.get("size"),
        "dwg_output_path": dwg_output.get("path"),
        "dwg_output_size": dwg_output.get("size"),
        "objects2d": counts.get("2d"),
        "operations3d": counts.get("3dOperations"),
        "variables": counts.get("variables"),
        "pages": counts.get("pages"),
        "output_errors": result.get("output_errors") or [],
        "error": result.get("error") or recipe_result.get("error"),
    }


def _summary(rows: list[dict[str, Any]], *, selected: int, dry_run: bool) -> dict[str, Any]:
    attempted = len(rows)
    passed = len([row for row in rows if row.get("ok")])
    failed = attempted - passed
    return {
        "dry_run": dry_run,
        "selected": selected,
        "attempted": attempted,
        "passed": passed,
        "failed": failed,
        "buckets": _buckets(rows),
    }


def _failure_kind(result: dict[str, Any]) -> str:
    if result.get("ok") is True:
        return "passed"
    output_errors = result.get("output_errors") or []
    if output_errors:
        return "export_failed"
    stage = str(result.get("stage") or "").lower()
    error = str(result.get("error") or "").lower()
    recipe_result = result.get("recipe_result") if isinstance(result.get("recipe_result"), dict) else {}
    recipe_stage = str(recipe_result.get("stage") or "").lower()
    if stage == "input" or recipe_stage == "input":
        return "input_failed"
    if stage == "timeout" or recipe_stage == "timeout" or "timeout" in error:
        return "timeout_failed"
    if recipe_result and recipe_result.get("ok") is False:
        return "recipe_failed"
    if stage in {"compile", "run"}:
        return "run_failed"
    return "unknown_failed"


def _buckets(rows: list[dict[str, Any]]) -> dict[str, int]:
    keys = [
        "passed",
        "input_failed",
        "timeout_failed",
        "export_failed",
        "recipe_failed",
        "run_failed",
        "unknown_failed",
    ]
    buckets = {key: 0 for key in keys}
    for row in rows:
        kind = row.get("failure_kind") or ("passed" if row.get("ok") else "unknown_failed")
        buckets[str(kind)] = buckets.get(str(kind), 0) + 1
    return buckets


def _failure_report(matrix: dict[str, Any]) -> dict[str, Any]:
    rows = matrix.get("rows") if isinstance(matrix.get("rows"), list) else []
    failed_rows = [row for row in rows if isinstance(row, dict) and row.get("ok") is not True]
    by_kind: dict[str, list[dict[str, Any]]] = {}
    for row in failed_rows:
        kind = str(row.get("failure_kind") or "unknown_failed")
        by_kind.setdefault(kind, []).append(_failure_row(row))
    failed_payloads = [item["payload_path"] for item in failed_rows if item.get("payload_path")]
    return {
        "ok": len(failed_rows) == 0,
        "summary": matrix.get("summary") or {},
        "selection": matrix.get("selection"),
        "payload_dir": matrix.get("payload_dir"),
        "failed_matrix": matrix.get("failed_matrix"),
        "audit_open_only": matrix.get("audit_open_only"),
        "failed_count": len(failed_rows),
        "failed_payloads": failed_payloads,
        "failed_by_kind": by_kind,
        "rerun_failed_hint": "python -m tflex_harness.cli document-factory-batch --failed-matrix <document_factory_batch_matrix.json>",
    }


def _failure_row(row: dict[str, Any]) -> dict[str, Any]:
    keys = [
        "index",
        "payload_name",
        "payload_path",
        "failure_kind",
        "stage",
        "recipe",
        "selection",
        "factory_run_dir",
        "audit_run_dir",
        "error",
        "output_errors",
    ]
    return {key: row.get(key) for key in keys if row.get(key) not in (None, [], {})}


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    fieldnames = [
        "index",
        "payload_name",
        "status",
        "ok",
        "failure_kind",
        "dry_run",
        "audit_open_only",
        "stage",
        "recipe",
        "selection",
        "output_path",
        "output_size",
        "step_output_path",
        "step_output_size",
        "pdf_output_path",
        "pdf_output_size",
        "dxf_output_path",
        "dxf_output_size",
        "dwg_output_path",
        "dwg_output_size",
        "objects2d",
        "operations3d",
        "variables",
        "pages",
        "factory_run_dir",
        "audit_run_dir",
        "payload_path",
        "error",
    ]
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
