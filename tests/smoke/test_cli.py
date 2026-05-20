import json
import os
import subprocess
import sys
from pathlib import Path


def _cli(*args: str, timeout: int = 60) -> dict:
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


def test_cli_search_returns_unified_results():
    result = _cli("search", "Document SaveAs", "--scope", "symbols", "--limit", "1")

    assert result["results"][0]["id"] == "M:TFlex.Model.Document.SaveAs(System.String)"
    assert result["results"][0]["scope"] == "symbols"


def test_cli_env_reports_runner_and_docs():
    result = _cli("env", timeout=90)

    assert result["docs"]["symbols_jsonl"] is True
    assert result["runner"]["build_ok"] is True
    assert result["dlls"]["TFlexAPI.dll"]["exists"] is True


def test_cli_recipes_lists_verified_sources():
    result = _cli("recipes")
    recipes = {recipe["name"]: recipe for recipe in result["recipes"]}

    assert recipes["environment_probe"]["verified"] is True
    assert recipes["environment_probe"]["source_path"].endswith("agent_workspace\\recipes\\environment_probe.cs")
    assert recipes["environment_probe"]["markdown_path"].endswith("agent_workspace\\recipes\\environment_probe.md")
    assert recipes["environment_probe"]["source_exists"] is True
    assert recipes["environment_probe"]["markdown_exists"] is True
    assert recipes["create_simple_3d_extrusion"]["verified"] is True


def test_cli_run_csharp_compile_only_returns_structured_result():
    code = 'public class Program { public static int Main(){ System.Console.WriteLine("cli-compile"); return 0; } }'
    result = _cli(
        "run-csharp",
        "--mode",
        "compile_only",
        "--timeout-sec",
        "30",
        "--artifact-prefix",
        "test_cli_compile_only",
        "--code",
        code,
        timeout=90,
    )

    assert result["ok"] is True, result
    assert result["stage"] == "compile"
    assert result["snippet_path"].endswith("snippet.cs")
