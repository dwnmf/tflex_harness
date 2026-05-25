from __future__ import annotations

from tflex_harness.prototype_validation import validate_open_copy_save_batch


def _write(path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def test_validate_open_copy_save_batch_dry_run_writes_matrix(tmp_path):
    root = tmp_path / "Прототипы"
    _write(root / "3D Деталь.grb", b"part")
    _write(root / "Чертежи" / "Чертёж детали.grb", b"drawing")
    out = tmp_path / "matrix"

    result = validate_open_copy_save_batch(root, dry_run=True, output_dir=out)

    assert result["ok"] is True
    assert result["summary"]["catalog_grb_count"] == 2
    assert result["summary"]["selected"] == 2
    assert result["summary"]["passed"] == 2
    assert result["rows"][0]["status"] == "dry_run"
    assert (out / "prototype_open_save_matrix.json").exists()
    assert (out / "prototype_open_save_matrix.csv").exists()


def test_validate_open_copy_save_batch_uses_recipe_runner(tmp_path):
    root = tmp_path / "Прототипы"
    _write(root / "3D Деталь.grb", b"part")
    calls = []

    def fake_runner(name, args, timeout_sec):
        calls.append((name, args, timeout_sec))
        return {
            "ok": True,
            "stage": "run",
            "phase": "run",
            "exit_code": 0,
            "run_dir": "artifacts/runs/demo",
            "stdout": "document.opened=True\ndocument.saved=True\ndocument.closed=True\neasy.session=False\n",
            "artifacts": [
                {"relative_path": "artifacts/prototype_copy.grb", "path": "copy.grb", "size": 4},
                {"relative_path": "artifacts/prototype_saved.grb", "path": "saved.grb", "size": 5},
            ],
        }

    result = validate_open_copy_save_batch(root, timeout_sec=77, output_dir=tmp_path / "out", recipe_runner=fake_runner)

    assert result["ok"] is True
    assert result["summary"]["passed"] == 1
    assert result["rows"][0]["opened"] is True
    assert result["rows"][0]["saved"] is True
    assert result["rows"][0]["closed"] is True
    assert result["rows"][0]["output_size"] == 5
    assert calls[0][0] == "prototype_open_copy_save"
    assert calls[0][1]["source_path"].endswith("3D Деталь.grb")
    assert calls[0][2] == 77


def test_validate_open_copy_save_batch_fail_fast(tmp_path):
    root = tmp_path / "Прототипы"
    _write(root / "A.grb", b"a")
    _write(root / "B.grb", b"b")

    def fake_runner(name, args, timeout_sec):
        return {
            "ok": False,
            "stage": "run",
            "phase": "run",
            "exit_code": 20,
            "stdout": "",
            "artifacts": [],
            "error": "failed",
        }

    result = validate_open_copy_save_batch(root, fail_fast=True, output_dir=tmp_path / "out", recipe_runner=fake_runner)

    assert result["ok"] is False
    assert result["summary"]["attempted"] == 1
    assert result["summary"]["failed"] == 1
