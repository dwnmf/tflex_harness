from __future__ import annotations

from tflex_harness.prototype_metadata import capture_metadata_batch, parse_metadata_stdout


def _write(path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def test_parse_metadata_stdout_extracts_counts_types_variables():
    stdout = "\n".join(
        [
            "document.opened=True",
            "document.title=Demo",
            "document.changed=False",
            "count.2d=12",
            "count.2dTextLike=3",
            "count.2dTableLike=1",
            "count.3dOperations=2",
            "count.variables=1",
            "count.pages=4",
            "object2dType=TFlex.Model.Model2D.Text|3",
            "operation3dType=TFlex.Model.Model3D.Block|2",
            "variable=0|Designation|False|True||ABC.001|\"ABC.001\"|comment|False|False|False",
        ]
    )

    metadata = parse_metadata_stdout(stdout)

    assert metadata["document"]["opened"] is True
    assert metadata["document"]["title"] == "Demo"
    assert metadata["counts"]["2d"] == 12
    assert metadata["counts"]["2dTextLike"] == 3
    assert metadata["counts"]["pages"] == 4
    assert metadata["object2d_types"]["TFlex.Model.Model2D.Text"] == 3
    assert metadata["operation3d_types"]["TFlex.Model.Model3D.Block"] == 2
    assert metadata["variables"][0]["name"] == "Designation"
    assert metadata["variables"][0]["text_value"] == "ABC.001"


def test_parse_metadata_stdout_preserves_unknown_backslash_escapes():
    stdout = "\n".join(
        [
            r"document.fileName=C:\Program Files\T-FLEX CAD 17\Program\Прототипы\2D Деталь.grb",
            r"document.title=Path C:\Temp\demo.grb",
        ]
    )

    metadata = parse_metadata_stdout(stdout)

    assert metadata["document"]["fileName"] == r"C:\Program Files\T-FLEX CAD 17\Program\Прототипы\2D Деталь.grb"
    assert metadata["document"]["title"] == r"Path C:\Temp\demo.grb"


def test_capture_metadata_batch_writes_index_and_per_prototype_files(tmp_path):
    root = tmp_path / "Прототипы"
    _write(root / "3D Деталь.grb", b"part")
    _write(root / "Чертежи" / "Чертёж детали.grb", b"drawing")
    out = tmp_path / "metadata"

    def fake_capture(prototype, timeout_sec):
        return {
            "ok": True,
            "prototype": prototype,
            "metadata": {
                "document": {"opened": True},
                "counts": {"2d": 10, "2dTextLike": 2, "2dTableLike": 1, "3dOperations": 0, "variables": 4, "pages": -1, "fragments": -1},
                "object2d_types": {},
                "operation3d_types": {},
                "variables": [],
                "errors": [],
            },
            "run": {"run_dir": "artifacts/runs/demo"},
        }

    result = capture_metadata_batch(root, output_dir=out, capture_func=fake_capture)

    assert result["ok"] is True
    assert result["summary"]["selected"] == 2
    assert result["summary"]["passed"] == 2
    assert result["rows"][0]["objects2d"] == 10
    assert (out / "prototype_metadata_index.json").exists()
    assert (out / "prototype_metadata_index.csv").exists()
    assert len(list((out / "metadata").glob("*.json"))) == 2


def test_capture_metadata_batch_filters_category(tmp_path):
    root = tmp_path / "Прототипы"
    _write(root / "3D Деталь.grb", b"part")
    _write(root / "Чертежи" / "Чертёж детали.grb", b"drawing")

    def fake_capture(prototype, timeout_sec):
        return {
            "ok": True,
            "prototype": prototype,
            "metadata": {"document": {"opened": True}, "counts": {}, "errors": []},
            "run": {},
        }

    result = capture_metadata_batch(root, category="Чертежи", output_dir=tmp_path / "out", capture_func=fake_capture)

    assert result["summary"]["selected"] == 1
    assert result["rows"][0]["category"] == "Чертежи"
