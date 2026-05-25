from __future__ import annotations

import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

from .artifacts import ArtifactStore, json_default
from .document_factory import create_document_from_payload


FactoryRunner = Callable[[Path, int, bool], dict[str, Any]]


DEFAULT_FACTORY_SAMPLES: tuple[dict[str, Any], ...] = (
    {
        "name": "3d_part_open_copy",
        "category": "3d_part",
        "payload": {
            "prototype": {"id": "3D Деталь"},
            "output": {"name": "factory_3d_part", "exports": ["grb"]},
            "document": {},
        },
    },
    {
        "name": "drawing_property",
        "category": "drawing",
        "payload": {
            "prototype": {"id": "Чертежи/Чертёж детали с форматкой"},
            "output": {"name": "factory_drawing", "exports": ["grb"]},
            "document": {"properties": {"Title": "Harness Drawing Factory"}},
        },
    },
    {
        "name": "specification_open_copy",
        "category": "specification",
        "payload": {
            "prototype": {"id": "Спецификации/Спецификация форма 1 ГОСТ 2.106-2019"},
            "output": {"name": "factory_specification", "exports": ["grb"]},
            "document": {},
        },
    },
    {
        "name": "table_cell",
        "category": "table",
        "payload": {
            "prototype": {"id": "Таблицы/Таблица параметров зубчатого колеса.grb"},
            "output": {"name": "factory_table", "exports": ["grb"]},
            "document": {"tables": [{"cell_index": 2, "text_value": "Harness Factory Table"}]},
        },
    },
)


def validate_document_factory_samples(
    *,
    timeout_sec: int = 120,
    dry_run: bool = False,
    fail_fast: bool = False,
    output_dir: str | Path | None = None,
    samples: list[dict[str, Any]] | tuple[dict[str, Any], ...] = DEFAULT_FACTORY_SAMPLES,
    factory_runner: FactoryRunner | None = None,
) -> dict[str, Any]:
    out = _output_dir(output_dir)
    payload_dir = out / "payloads"
    payload_dir.mkdir(parents=True, exist_ok=True)
    runner = factory_runner or _factory_runner_adapter
    rows: list[dict[str, Any]] = []

    for index, sample in enumerate(samples, start=1):
        row = _base_row(index, sample, dry_run=dry_run)
        payload_path = payload_dir / f"{index:02d}_{sample['name']}.json"
        payload_path.write_text(json.dumps(sample["payload"], ensure_ascii=False, indent=2, default=json_default) + "\n", encoding="utf-8")
        row["payload_path"] = str(payload_path)
        result = runner(payload_path, timeout_sec, dry_run)
        row.update(_result_to_row(result))
        rows.append(row)
        if fail_fast and not row["ok"]:
            break

    summary = _summary(rows, selected=len(samples), dry_run=dry_run)
    matrix = {
        "ok": summary["failed"] == 0,
        "summary": summary,
        "rows": rows,
    }
    matrix_path = out / "document_factory_samples_matrix.json"
    csv_path = out / "document_factory_samples_matrix.csv"
    matrix_path.write_text(json.dumps(matrix, ensure_ascii=False, indent=2, default=json_default) + "\n", encoding="utf-8")
    _write_csv(csv_path, rows)
    matrix["matrix_path"] = str(matrix_path)
    matrix["csv_path"] = str(csv_path)
    matrix["payload_dir"] = str(payload_dir)
    return matrix


def _factory_runner_adapter(payload_path: Path, timeout_sec: int, dry_run: bool) -> dict[str, Any]:
    return create_document_from_payload(payload_path, timeout_sec=timeout_sec, dry_run=dry_run)


def _output_dir(output_dir: str | Path | None) -> Path:
    if output_dir is not None:
        out = Path(output_dir)
    else:
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        out = ArtifactStore().root / "document_factory_validation" / stamp
    out.mkdir(parents=True, exist_ok=True)
    return out


def _base_row(index: int, sample: dict[str, Any], *, dry_run: bool) -> dict[str, Any]:
    payload = sample["payload"]
    return {
        "index": index,
        "name": sample["name"],
        "category": sample["category"],
        "prototype": payload["prototype"],
        "output": payload.get("output"),
        "dry_run": dry_run,
    }


def _result_to_row(result: dict[str, Any]) -> dict[str, Any]:
    plan = result.get("plan") if isinstance(result.get("plan"), dict) else {}
    recipe_result = result.get("recipe_result") if isinstance(result.get("recipe_result"), dict) else {}
    outputs = result.get("outputs") if isinstance(result.get("outputs"), list) else []
    first_output = outputs[0] if outputs else {}
    return {
        "status": "passed" if result.get("ok") else "failed",
        "ok": bool(result.get("ok")),
        "stage": result.get("stage"),
        "factory_run_dir": result.get("factory_run_dir"),
        "recipe": result.get("recipe") or plan.get("recipe"),
        "selection": plan.get("selection"),
        "planned_output": plan.get("output"),
        "output_path": first_output.get("path"),
        "output_size": first_output.get("size"),
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
        "name",
        "category",
        "status",
        "ok",
        "stage",
        "recipe",
        "selection",
        "output_path",
        "output_size",
        "factory_run_dir",
        "payload_path",
        "error",
    ]
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
