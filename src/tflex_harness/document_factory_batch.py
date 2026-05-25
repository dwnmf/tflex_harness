from __future__ import annotations

import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

from .artifacts import ArtifactStore, json_default
from .document_factory import create_document_from_payload


FactoryRunner = Callable[[Path, int, bool], dict[str, Any]]


def create_documents_from_payload_dir(
    payload_dir: str | Path,
    *,
    pattern: str = "*.json",
    recursive: bool = False,
    timeout_sec: int = 120,
    dry_run: bool = False,
    fail_fast: bool = False,
    output_dir: str | Path | None = None,
    factory_runner: FactoryRunner | None = None,
) -> dict[str, Any]:
    source_dir = Path(payload_dir).resolve()
    if not source_dir.exists():
        return {"ok": False, "stage": "input", "error": "payload directory does not exist", "payload_dir": str(source_dir)}
    if not source_dir.is_dir():
        return {"ok": False, "stage": "input", "error": "payload path is not a directory", "payload_dir": str(source_dir)}
    if not pattern:
        return {"ok": False, "stage": "input", "error": "pattern is required", "payload_dir": str(source_dir)}

    payloads = _payload_paths(source_dir, pattern=pattern, recursive=recursive)
    out = _output_dir(output_dir)
    runner = factory_runner or _factory_runner_adapter
    rows: list[dict[str, Any]] = []

    for index, payload_path in enumerate(payloads, start=1):
        result = runner(payload_path, timeout_sec, dry_run)
        row = _row_from_result(index, payload_path, result, dry_run=dry_run)
        rows.append(row)
        if fail_fast and not row["ok"]:
            break

    summary = _summary(rows, selected=len(payloads), dry_run=dry_run)
    matrix = {
        "ok": summary["failed"] == 0,
        "stage": "dry_run" if dry_run else "run",
        "payload_dir": str(source_dir),
        "pattern": pattern,
        "recursive": recursive,
        "summary": summary,
        "rows": rows,
    }
    matrix_path = out / "document_factory_batch_matrix.json"
    csv_path = out / "document_factory_batch_matrix.csv"
    matrix_path.write_text(json.dumps(matrix, ensure_ascii=False, indent=2, default=json_default) + "\n", encoding="utf-8")
    _write_csv(csv_path, rows)
    matrix["matrix_path"] = str(matrix_path)
    matrix["csv_path"] = str(csv_path)
    return matrix


def _factory_runner_adapter(payload_path: Path, timeout_sec: int, dry_run: bool) -> dict[str, Any]:
    return create_document_from_payload(payload_path, timeout_sec=timeout_sec, dry_run=dry_run)


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
    return {
        "index": index,
        "payload_name": payload_path.stem,
        "payload_path": str(payload_path),
        "status": "passed" if result.get("ok") else "failed",
        "ok": bool(result.get("ok")),
        "dry_run": dry_run,
        "stage": result.get("stage"),
        "factory_run_dir": result.get("factory_run_dir"),
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
    }


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    fieldnames = [
        "index",
        "payload_name",
        "status",
        "ok",
        "dry_run",
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
        "factory_run_dir",
        "payload_path",
        "error",
    ]
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
