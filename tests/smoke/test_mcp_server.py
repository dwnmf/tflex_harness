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
        "capture_tflex_state",
        "save_tflex_snippet_candidate",
    }.issubset(by_name)

    docs_schema = by_name["search_tflex_docs"].inputSchema
    assert "query" in docs_schema["required"]
    assert docs_schema["properties"]["scope"]["default"] == "all"

    runner_schema = by_name["run_csharp_tflex"].inputSchema
    assert "code" in runner_schema["required"]
    assert runner_schema["properties"]["mode"]["default"] == "run"
    assert runner_schema["properties"]["timeout_sec"]["default"] == 30

    recipe_schema = by_name["run_tflex_recipe"].inputSchema
    assert "recipe" in recipe_schema["required"]
    assert recipe_schema["properties"]["timeout_sec"]["default"] == 60


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
