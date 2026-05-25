from __future__ import annotations

import json

from tflex_harness.document_factory import create_document_from_payload, plan_document_creation


def test_plan_document_creation_dispatches_property_payload():
    payload = {
        "prototype": {"id": "2D Деталь"},
        "document": {"properties": {"Title": "Demo"}},
    }

    plan = plan_document_creation(payload)

    assert plan["ok"] is True
    assert plan["recipe"] == "prototype_set_document_property"
    assert plan["recipe_args"] == {"prototype_id": "2D Деталь", "property_name": "Title", "text_value": "Demo"}
    assert plan["selection"] == "document.properties"


def test_plan_document_creation_dispatches_numeric_variable_payload():
    payload = {
        "prototype": {"id": "2D Деталь"},
        "document": {"variables": {"Nomer_Shem": 42}},
    }

    plan = plan_document_creation(payload)

    assert plan["recipe"] == "prototype_set_real_variable"
    assert plan["recipe_args"]["real_value"] == "42"


def test_plan_document_creation_uses_multi_step_for_multiple_groups():
    payload = {
        "prototype": {"id": "Электротехника/Клеммник.grb"},
        "document": {
            "properties": {"Title": "Demo"},
            "text_replacements": {"Цепь": "Harness Circuit"},
        },
    }

    plan = plan_document_creation(payload)

    assert plan["recipe"] == "__factory_multi_step"
    assert plan["selection"] == "multi_step"
    assert plan["pending_operations"] == []
    assert plan["operations"] == [
        {"type": "property", "name": "Title", "value": "Demo"},
        {"type": "visible_text", "search": "Цепь", "replacement": "Harness Circuit"},
    ]


def test_plan_document_creation_uses_multi_step_for_multiple_variables():
    payload = {
        "prototype": {"id": "2D Деталь"},
        "document": {
            "variables": {"Nomer_Shem": 42, "$Наименование": "Demo"},
        },
    }

    plan = plan_document_creation(payload)

    assert plan["recipe"] == "__factory_multi_step"
    assert [operation["type"] for operation in plan["operations"]] == ["real_variable", "text_variable"]


def test_create_document_from_payload_dry_run_writes_factory_artifacts(tmp_path):
    payload_path = tmp_path / "payload.json"
    payload_path.write_text(
        json.dumps({"prototype": {"id": "2D Деталь"}, "document": {"properties": {"Title": "Demo"}}}, ensure_ascii=False),
        encoding="utf-8",
    )

    result = create_document_from_payload(payload_path, dry_run=True)

    assert result["ok"] is True
    assert result["stage"] == "dry_run"
    assert result["plan"]["recipe"] == "prototype_set_document_property"
    assert result["input_payload_path"].endswith("input_payload.json")
    assert result["plan_path"].endswith("factory_plan.json")


def test_plan_document_creation_rejects_non_integer_cell_index():
    payload = {
        "prototype": {"id": "Таблицы/Таблица параметров зубчатого колеса.grb"},
        "document": {"tables": [{"cell_index": "bad", "text_value": "x"}]},
    }

    plan = plan_document_creation(payload)

    assert plan["ok"] is False
    assert plan["error"] == "document.tables[0].cell_index must be an integer"


def test_create_document_from_payload_uses_recipe_runner(tmp_path):
    payload_path = tmp_path / "payload.json"
    payload_path.write_text(
        json.dumps({"prototype": {"id": "2D Деталь"}, "document": {"variables": {"Nomer_Shem": 42}}}, ensure_ascii=False),
        encoding="utf-8",
    )
    calls = []

    def fake_runner(name, args, timeout_sec, config):
        calls.append((name, args, timeout_sec, config))
        return {"ok": True, "stage": "run", "run_dir": "artifacts/runs/fake"}

    result = create_document_from_payload(payload_path, timeout_sec=7, recipe_runner=fake_runner)

    assert result["ok"] is True
    assert result["recipe"] == "prototype_set_real_variable"
    assert calls[0][0] == "prototype_set_real_variable"
    assert calls[0][1]["variable_name"] == "Nomer_Shem"
    assert calls[0][2] == 7
