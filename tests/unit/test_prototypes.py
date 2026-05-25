from __future__ import annotations

import hashlib

import pytest

from tflex_harness.prototypes import (
    find_prototype,
    list_prototypes,
    prototype_info,
    scan_and_write_catalog,
    scan_prototypes,
)


def _write(path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def test_scan_prototypes_indexes_cyrillic_tree(tmp_path):
    _write(tmp_path / "3D Деталь.grb", b"root-grb")
    _write(tmp_path / "Спецификации" / "Форма ведомости.grb", b"spec-grb")
    _write(tmp_path / "Таблицы" / "TemplateSettings.xml", b"<xml/>")
    _write(tmp_path / "skip.bin", b"ignored")

    catalog = scan_prototypes(tmp_path)

    assert catalog["ok"] is True
    assert catalog["file_count"] == 3
    assert catalog["grb_count"] == 2
    assert catalog["counts_by_extension"] == {".grb": 2, ".xml": 1}
    assert catalog["counts_by_category"] == {"root": 1, "Спецификации": 1, "Таблицы": 1}

    ids = {item["id"] for item in catalog["files"]}
    assert "3D Деталь" in ids
    assert "Спецификации/Форма ведомости" in ids


def test_find_prototype_by_id_name_relative_and_absolute(tmp_path):
    target = tmp_path / "Чертежи" / "Чертёж детали с форматкой.grb"
    _write(target, b"drawing-grb")

    by_id = find_prototype("Чертежи/Чертёж детали с форматкой", tmp_path)
    by_name = find_prototype("Чертёж детали с форматкой.grb", tmp_path)
    by_relative = find_prototype("Чертежи\\Чертёж детали с форматкой.grb", tmp_path)
    by_absolute = find_prototype(str(target), tmp_path)

    assert by_id == by_name == by_relative == by_absolute
    assert by_id["sha256"] == hashlib.sha256(b"drawing-grb").hexdigest()


def test_prototype_info_raises_for_unknown_selector(tmp_path):
    with pytest.raises(KeyError):
        prototype_info("missing", tmp_path)


def test_list_prototypes_filters_category_extension_and_limit(tmp_path):
    _write(tmp_path / "3D Деталь.grb", b"a")
    _write(tmp_path / "Спецификации" / "А.grb", b"b")
    _write(tmp_path / "Спецификации" / "Б.xml", b"c")

    spec_grb = list_prototypes(tmp_path, category="Спецификации", extension=".grb")
    all_supported = list_prototypes(tmp_path, extension=None, limit=2)

    assert spec_grb["count"] == 1
    assert spec_grb["files"][0]["id"] == "Спецификации/А"
    assert all_supported["count"] == 2


def test_scan_and_write_catalog(tmp_path):
    root = tmp_path / "Прототипы"
    out = tmp_path / "catalog_out"
    _write(root / "2D Деталь.grb", b"part")

    result = scan_and_write_catalog(root, output_dir=out)

    assert result["ok"] is True
    assert result["grb_count"] == 1
    assert (out / "catalog.json").exists()
