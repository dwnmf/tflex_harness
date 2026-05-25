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


def test_cli_search_accepts_known_assembly_filter():
    result = _cli("search", "Document SaveAs", "--scope", "symbols", "--assembly", "TFlexAPI", "--limit", "1")

    assert result["assembly"] == "TFlexAPI"
    assert result["results"][0]["assembly"] == "TFlexAPI"


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


def test_cli_run_csharp_accepts_known_reference():
    code = "using TFlex; public class Program { public static int Main(){ ApplicationSessionSetup setup = null; return setup == null ? 0 : 1; } }"
    result = _cli(
        "run-csharp",
        "--mode",
        "compile_only",
        "--timeout-sec",
        "30",
        "--artifact-prefix",
        "test_cli_compile_tflex_reference",
        "--reference",
        "TFlexAPI",
        "--code",
        code,
        timeout=90,
    )

    assert result["ok"] is True, result
    assert result["resolved_references"][0]["name"] == "TFlexAPI"


def test_cli_run_csharp_compile_only_accepts_helpers():
    code = 'using TFlexEasy; public class Program { public static int Main(){ System.Console.WriteLine(EasyUnits.F(EasyUnits.ModelToMm(0.042))); return 0; } }'
    result = _cli(
        "run-csharp",
        "--mode",
        "compile_only",
        "--timeout-sec",
        "30",
        "--artifact-prefix",
        "test_cli_compile_helpers",
        "--helper",
        "easy_core",
        "--code",
        code,
        timeout=90,
    )

    assert result["ok"] is True, result
    assert result["stage"] == "compile"
    assert [helper["name"] for helper in result["helper_sources"]] == ["TFlexEasyUnits.cs", "TFlexEasyDiagnostics.cs"]


def test_cli_run_csharp_compile_only_accepts_all_helpers():
    code = 'using TFlexEasy; public class Program { public static int Main(){ System.Console.WriteLine(EasyUnits.F(1.0)); return 0; } }'
    result = _cli(
        "run-csharp",
        "--mode",
        "compile_only",
        "--timeout-sec",
        "60",
        "--artifact-prefix",
        "test_cli_compile_all_helpers",
        "--helper",
        "all",
        "--code",
        code,
        timeout=90,
    )

    assert result["ok"] is True, result
    assert result["stage"] == "compile"
    assert len(result["helper_sources"]) == 9


def test_cli_reverse_evidence_writes_semantic_outputs(tmp_path):
    result = _cli(
        "reverse-evidence",
        "agent_workspace/snippets/grb_reverse_planetary/model_evidence_with_contours.json",
        "--output-dir",
        str(tmp_path),
    )

    assert result["ok"] is True
    assert result["recognized_count"] == 9
    assert (tmp_path / "semantic_model.json").exists()
    assert (tmp_path / "parametric_candidate.cs").exists()


def test_cli_prototypes_scan_list_info(tmp_path):
    root = tmp_path / "Прототипы"
    root.mkdir()
    (root / "3D Деталь.grb").write_bytes(b"root-grb")
    specs = root / "Спецификации"
    specs.mkdir()
    (specs / "Спецификация форма 1.grb").write_bytes(b"spec-grb")
    out = tmp_path / "catalog"

    scan = _cli("prototypes-scan", "--root", str(root), "--output-dir", str(out))

    assert scan["ok"] is True
    assert scan["grb_count"] == 2
    assert Path(scan["catalog_path"]).exists()

    listed = _cli("prototypes-list", "--root", str(root), "--category", "Спецификации")
    assert listed["count"] == 1
    assert listed["files"][0]["id"] == "Спецификации/Спецификация форма 1"

    info = _cli("prototypes-info", "Спецификации/Спецификация форма 1", "--root", str(root))
    assert info["ok"] is True
    assert info["prototype"]["name"] == "Спецификация форма 1.grb"
