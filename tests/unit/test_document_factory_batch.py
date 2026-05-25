from __future__ import annotations

import json
from pathlib import Path

from tflex_harness.document_factory_batch import create_documents_from_payload_dir


def _write_payload(path: Path, title: str = "Batch") -> None:
    path.write_text(
        json.dumps(
            {
                "prototype": {"id": "2D Деталь"},
                "output": {"name": path.stem, "exports": ["grb"]},
                "document": {"properties": {"Title": title}},
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )


def test_create_documents_from_payload_dir_writes_matrix_and_csv(tmp_path):
    payload_dir = tmp_path / "payloads"
    payload_dir.mkdir()
    _write_payload(payload_dir / "b.json", "B")
    _write_payload(payload_dir / "a.json", "A")
    calls = []

    def fake_runner(payload_path: Path, timeout_sec: int, dry_run: bool):
        calls.append((payload_path.name, timeout_sec, dry_run))
        return {
            "ok": True,
            "stage": "dry_run",
            "factory_run_dir": f"artifacts/runs/{payload_path.stem}",
            "plan": {
                "recipe": "prototype_set_document_property",
                "selection": "document.properties",
                "output": {"name": payload_path.stem, "exports": ["grb"]},
            },
        }

    result = create_documents_from_payload_dir(
        payload_dir,
        timeout_sec=9,
        dry_run=True,
        output_dir=tmp_path / "out",
        factory_runner=fake_runner,
    )

    assert result["ok"] is True
    assert result["summary"] == {"dry_run": True, "selected": 2, "attempted": 2, "passed": 2, "failed": 0}
    assert [row["payload_name"] for row in result["rows"]] == ["a", "b"]
    assert result["rows"][0]["recipe"] == "prototype_set_document_property"
    assert calls == [("a.json", 9, True), ("b.json", 9, True)]
    assert Path(result["matrix_path"]).exists()
    assert Path(result["csv_path"]).exists()


def test_create_documents_from_payload_dir_fail_fast(tmp_path):
    payload_dir = tmp_path / "payloads"
    payload_dir.mkdir()
    _write_payload(payload_dir / "one.json")
    _write_payload(payload_dir / "two.json")

    def fake_runner(payload_path: Path, timeout_sec: int, dry_run: bool):
        return {"ok": False, "stage": "input", "error": "boom"}

    result = create_documents_from_payload_dir(
        payload_dir,
        fail_fast=True,
        output_dir=tmp_path / "out",
        factory_runner=fake_runner,
    )

    assert result["ok"] is False
    assert result["summary"]["selected"] == 2
    assert result["summary"]["attempted"] == 1
    assert result["summary"]["failed"] == 1
    assert result["rows"][0]["error"] == "boom"


def test_create_documents_from_payload_dir_recursive_glob(tmp_path):
    payload_dir = tmp_path / "payloads"
    nested = payload_dir / "nested"
    nested.mkdir(parents=True)
    _write_payload(nested / "child.payload.json")
    (payload_dir / "skip.json").write_text("{}", encoding="utf-8")
    calls = []

    def fake_runner(payload_path: Path, timeout_sec: int, dry_run: bool):
        calls.append(payload_path.name)
        return {"ok": True, "stage": "dry_run", "plan": {"recipe": "prototype_open_copy_save"}}

    result = create_documents_from_payload_dir(
        payload_dir,
        pattern="*.payload.json",
        recursive=True,
        dry_run=True,
        output_dir=tmp_path / "out",
        factory_runner=fake_runner,
    )

    assert result["ok"] is True
    assert result["summary"]["selected"] == 1
    assert calls == ["child.payload.json"]


def test_create_documents_from_payload_dir_rejects_missing_dir(tmp_path):
    result = create_documents_from_payload_dir(tmp_path / "missing")

    assert result["ok"] is False
    assert result["stage"] == "input"
    assert result["error"] == "payload directory does not exist"
