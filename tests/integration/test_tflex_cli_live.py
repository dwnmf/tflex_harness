import json
import os
import subprocess
import sys
from pathlib import Path

import pytest


def _cli(*args: str, timeout: int = 90) -> dict:
    env = os.environ.copy()
    src = str(Path.cwd() / "src")
    env["PYTHONPATH"] = src + os.pathsep + env.get("PYTHONPATH", "")
    proc = subprocess.run(
        [sys.executable, "-m", "tflex_harness.cli", *args],
        text=True,
        capture_output=True,
        timeout=timeout,
        env=env,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    return json.loads(proc.stdout)


@pytest.mark.integration
def test_cli_run_recipe_environment_probe_live():
    result = _cli("run-recipe", "environment_probe", "--timeout-sec", "60")

    assert result["ok"] is True, result
    assert result["recipe"] == "environment_probe"
    assert "init=True" in result["stdout"]


@pytest.mark.integration
def test_cli_state_live_returns_observable_session():
    state = _cli("state", "--timeout-sec", "60")

    assert state["ok"] is True, state
    assert state["session_initialized"] is True
    assert isinstance(state["documents"], list)
    assert isinstance(state["object_counts"], dict)
