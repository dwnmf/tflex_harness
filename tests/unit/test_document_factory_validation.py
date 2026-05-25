from __future__ import annotations

import json
from pathlib import Path

from tflex_harness.document_factory_validation import validate_document_factory_samples


def test_validate_document_factory_samples_writes_payloads_matrix_and_csv(tmp_path):
    samples = [
        {
            "name": "sample",
            "category": "unit",
            "payload": {
                "prototype": {"id": "2D Деталь"},
                "output": {"name": "unit_sample", "exports": ["grb"]},
                "document": {},
            },
        }
    ]
    calls = []

    def fake_runner(payload_path: Path, timeout_sec: int, dry_run: bool):
        calls.append((payload_path, timeout_sec, dry_run))
        return {
            "ok": True,
            "stage": "dry_run",
            "factory_run_dir": "artifacts/runs/factory",
            "plan": {
                "recipe": "prototype_open_copy_save",
                "selection": "open_copy_save",
                "output": {"name": "unit_sample", "exports": ["grb"]},
            },
        }

    result = validate_document_factory_samples(
        timeout_sec=7,
        dry_run=True,
        output_dir=tmp_path / "out",
        samples=samples,
        factory_runner=fake_runner,
    )

    assert result["ok"] is True
    assert result["summary"]["passed"] == 1
    assert result["rows"][0]["recipe"] == "prototype_open_copy_save"
    assert calls[0][1:] == (7, True)
    assert Path(result["matrix_path"]).exists()
    assert Path(result["csv_path"]).exists()
    payload_path = Path(result["payload_dir"]) / "01_sample.json"
    assert json.loads(payload_path.read_text(encoding="utf-8"))["output"]["name"] == "unit_sample"


def test_validate_document_factory_samples_fail_fast(tmp_path):
    samples = [
        {"name": "bad", "category": "unit", "payload": {"prototype": {"id": "bad"}, "document": {}}},
        {"name": "skip", "category": "unit", "payload": {"prototype": {"id": "skip"}, "document": {}}},
    ]

    def fake_runner(payload_path: Path, timeout_sec: int, dry_run: bool):
        return {"ok": False, "stage": "input", "error": "boom"}

    result = validate_document_factory_samples(
        fail_fast=True,
        output_dir=tmp_path / "out",
        samples=samples,
        factory_runner=fake_runner,
    )

    assert result["ok"] is False
    assert result["summary"]["attempted"] == 1
    assert result["summary"]["failed"] == 1
