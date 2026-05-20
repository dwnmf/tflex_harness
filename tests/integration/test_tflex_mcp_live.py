import asyncio
import json

import pytest

from tflex_harness.mcp_server import create_server


def _run(coro):
    return asyncio.run(coro)


def _json_payload(content):
    assert content
    return json.loads(content[0].text)


def test_mcp_run_recipe_environment_probe_live():
    pytest.importorskip("mcp")

    server = create_server()
    result = _json_payload(
        _run(
            server.call_tool(
                "run_tflex_recipe",
                {"recipe": "environment_probe", "timeout_sec": 60},
            )
        )
    )

    assert result["ok"] is True, result
    assert result["recipe"] == "environment_probe"
    assert "init=True" in result["stdout"]


def test_mcp_capture_state_live():
    pytest.importorskip("mcp")

    server = create_server()
    state = _json_payload(
        _run(server.call_tool("capture_tflex_state", {"timeout_sec": 60}))
    )

    assert state["ok"] is True, state
    assert state["session_initialized"] is True
    assert isinstance(state["documents"], list)
    assert isinstance(state["object_counts"], dict)
