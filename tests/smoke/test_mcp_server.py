import asyncio
import json

import pytest

from tflex_harness.mcp_server import create_server


def _run(coro):
    return asyncio.run(coro)


def _json_payload(content):
    assert content
    return json.loads(content[0].text)


def test_mcp_server_lists_core_tools_and_schemas():
    pytest.importorskip("mcp")

    server = create_server()
    tools = _run(server.list_tools())
    by_name = {tool.name: tool for tool in tools}

    assert {
        "search_tflex_docs",
        "get_tflex_environment",
        "run_csharp_tflex",
        "list_tflex_recipes",
        "run_tflex_recipe",
        "create_tflex_document",
        "run_tflex_document_factory_batch",
        "capture_tflex_state",
        "save_tflex_snippet_candidate",
    }.issubset(by_name)

    docs_schema = by_name["search_tflex_docs"].inputSchema
    assert "query" in docs_schema["required"]
    assert docs_schema["properties"]["scope"]["default"] == "all"
    assert docs_schema["properties"]["scope"]["enum"] == ["symbols", "types", "chm", "all"]
    assembly_schema = docs_schema["properties"]["assembly"]["anyOf"][0]
    assert assembly_schema["enum"] == ["TFlexAPI", "TFlexAPI3D", "TFlexAPIData", "TFlexCommandAPI"]

    runner_schema = by_name["run_csharp_tflex"].inputSchema
    assert "code" in runner_schema["required"]
    assert runner_schema["properties"]["mode"]["default"] == "run"
    assert runner_schema["properties"]["mode"]["enum"] == ["compile_only", "run"]
    assert runner_schema["properties"]["timeout_sec"]["default"] == 30
    references_schema = runner_schema["properties"]["references"]["anyOf"][0]["items"]
    assert references_schema["enum"] == ["TFlexAPI", "TFlexAPI3D", "TFlexAPIData", "TFlexCommandAPI"]
    assert "helpers" in runner_schema["properties"]

    recipe_schema = by_name["run_tflex_recipe"].inputSchema
    assert "recipe" in recipe_schema["required"]
    assert recipe_schema["properties"]["timeout_sec"]["default"] == 60

    create_doc_schema = by_name["create_tflex_document"].inputSchema
    assert "payload_path" in create_doc_schema["required"]
    assert create_doc_schema["properties"]["timeout_sec"]["default"] == 120
    assert create_doc_schema["properties"]["dry_run"]["default"] is False

    batch_schema = by_name["run_tflex_document_factory_batch"].inputSchema
    assert batch_schema["properties"]["pattern"]["default"] == "*.json"
    assert batch_schema["properties"]["dry_run"]["default"] is False
    assert "failed_matrix" in batch_schema["properties"]
    assert "audit_open_only" in batch_schema["properties"]


def test_mcp_docs_and_recipe_tools_return_machine_readable_payloads():
    pytest.importorskip("mcp")

    server = create_server()

    docs = _json_payload(
        _run(
            server.call_tool(
                "search_tflex_docs",
                {"query": "Document SaveAs", "scope": "symbols", "limit": 1},
            )
        )
    )
    assert docs["results"][0]["scope"] == "symbols"
    assert docs["results"][0]["id"] == "M:TFlex.Model.Document.SaveAs(System.String)"
    assert docs["symbols"][0]["id"] == "M:TFlex.Model.Document.SaveAs(System.String)"

    recipes = _json_payload(_run(server.call_tool("list_tflex_recipes", {})))
    names = {recipe["name"] for recipe in recipes["recipes"]}
    assert {
        "environment_probe",
        "save_document_as_temp",
        "create_simple_3d_extrusion",
    }.issubset(names)
    by_name = {recipe["name"]: recipe for recipe in recipes["recipes"]}
    assert by_name["environment_probe"]["source_path"].endswith("environment_probe.cs")
    assert by_name["environment_probe"]["markdown_path"].endswith("environment_probe.md")
    assert by_name["environment_probe"]["source_exists"] is True
    assert by_name["environment_probe"]["markdown_exists"] is True

    missing_recipe = _json_payload(
        _run(server.call_tool("run_tflex_recipe", {"recipe": "missing_recipe", "timeout_sec": 1}))
    )
    assert missing_recipe["ok"] is False
    assert missing_recipe["stage"] == "input"
    assert missing_recipe["error"] == "unknown recipe"


def test_mcp_document_factory_tools_return_machine_readable_payloads(tmp_path):
    pytest.importorskip("mcp")

    server = create_server()
    payload_dir = tmp_path / "payloads"
    payload_dir.mkdir()
    payload = payload_dir / "doc.json"
    payload.write_text(
        json.dumps(
            {
                "prototype": {"id": "2D Деталь"},
                "document": {"properties": {"Title": "MCP Factory"}},
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    single = _json_payload(
        _run(
            server.call_tool(
                "create_tflex_document",
                {"payload_path": str(payload), "dry_run": True},
            )
        )
    )
    assert single["ok"] is True
    assert single["stage"] == "dry_run"
    assert single["plan"]["recipe"] == "prototype_set_document_property"

    batch = _json_payload(
        _run(
            server.call_tool(
                "run_tflex_document_factory_batch",
                {"payload_dir": str(payload_dir), "dry_run": True, "output_dir": str(tmp_path / "batch")},
            )
        )
    )
    assert batch["ok"] is True
    assert batch["summary"]["selected"] == 1
    assert batch["rows"][0]["recipe"] == "prototype_set_document_property"
    assert batch["failure_report_path"].endswith("document_factory_failure_report.json")
