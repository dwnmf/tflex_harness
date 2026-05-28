import json
import os
import subprocess
import sys
from pathlib import Path

from tflex_harness.runner import HELPER_SETS


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


def test_cli_doctor_reports_install_checks():
    result = _cli("doctor", timeout=90)

    assert "checks" in result
    assert result["score"]["total"] == len(result["checks"])
    assert {item["name"] for item in result["checks"]} >= {"tflex_install_dir", "tflex_api_docs", "repo_workspace", "runner"}


def test_cli_mcp_config_prints_ready_json():
    result = _cli("mcp-config", "--for", "codex")
    server = result["mcpServers"]["tflex-harness"]

    assert result["client"] == "codex"
    assert server["command"] == "tflex-harness-mcp"
    assert server["env"]["TFLEX_HARNESS_REPO_DIR"].endswith("tflex_harness")
    assert server["env"]["TFLEX_API_DOCS_DIR"].endswith("tflex_api")


def test_cli_bootstrap_dry_path_has_no_external_side_effects():
    result = _cli("bootstrap", "--no-docs", "--no-checks")

    assert result["ok"] is True
    assert result["repo_dir"].endswith("tflex_harness")
    assert result["docs_dir"].endswith("tflex_api")
    assert result["persist_env"] is False
    assert result["env"] == []
    assert result["skill"] is None


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
    assert len(result["helper_sources"]) == len(HELPER_SETS["all"])


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


def test_cli_prototypes_open_save_batch_dry_run(tmp_path):
    root = tmp_path / "Прототипы"
    root.mkdir()
    (root / "3D Деталь.grb").write_bytes(b"root-grb")
    drawings = root / "Чертежи"
    drawings.mkdir()
    (drawings / "Чертёж детали.grb").write_bytes(b"drawing-grb")
    out = tmp_path / "batch"

    result = _cli("prototypes-open-save-batch", "--root", str(root), "--dry-run", "--output-dir", str(out))

    assert result["ok"] is True
    assert result["summary"]["selected"] == 2
    assert result["summary"]["passed"] == 2
    assert Path(result["matrix_path"]).exists()
    assert Path(result["csv_path"]).exists()


def test_cli_prototypes_metadata_with_empty_fake_tree(tmp_path):
    root = tmp_path / "Прототипы"
    root.mkdir()
    out = tmp_path / "metadata"

    result = _cli("prototypes-metadata", "--root", str(root), "--output-dir", str(out))

    assert result["ok"] is True
    assert result["summary"]["selected"] == 0
    assert result["summary"]["passed"] == 0
    assert Path(result["index_path"]).exists()
    assert Path(result["csv_path"]).exists()
    assert Path(result["metadata_dir"]).exists()


def test_cli_create_document_dry_run_dispatches_payload(tmp_path):
    payload = tmp_path / "payload.json"
    payload.write_text(
        json.dumps(
            {
                "prototype": {"id": "2D Деталь"},
                "document": {"properties": {"Title": "Smoke"}},
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    result = _cli("create-document", "--payload", str(payload), "--dry-run")

    assert result["ok"] is True
    assert result["stage"] == "dry_run"
    assert result["plan"]["recipe"] == "prototype_set_document_property"
    assert Path(result["input_payload_path"]).exists()
    assert Path(result["plan_path"]).exists()


def test_cli_document_factory_samples_dry_run(tmp_path):
    out = tmp_path / "factory_samples"

    result = _cli("document-factory-samples", "--dry-run", "--output-dir", str(out))

    assert result["ok"] is True
    assert result["summary"]["selected"] == 4
    assert result["summary"]["passed"] == 4
    assert Path(result["matrix_path"]).exists()
    assert Path(result["csv_path"]).exists()
    assert Path(result["payload_dir"]).exists()


def test_cli_document_factory_batch_dry_run(tmp_path):
    payload_dir = tmp_path / "payloads"
    payload_dir.mkdir()
    payload = payload_dir / "drawing.json"
    payload.write_text(
        json.dumps(
            {
                "prototype": {"id": "2D Деталь"},
                "document": {"properties": {"Title": "Batch Smoke"}},
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    out = tmp_path / "factory_batch"

    result = _cli("document-factory-batch", "--payload-dir", str(payload_dir), "--dry-run", "--output-dir", str(out))

    assert result["ok"] is True
    assert result["summary"]["selected"] == 1
    assert result["summary"]["passed"] == 1
    assert result["rows"][0]["recipe"] == "prototype_set_document_property"
    assert result["rows"][0]["failure_kind"] == "passed"
    assert Path(result["matrix_path"]).exists()
    assert Path(result["csv_path"]).exists()
    assert Path(result["failure_report_path"]).exists()


def test_cli_document_factory_batch_rerun_failed_dry_run(tmp_path):
    payload_dir = tmp_path / "payloads"
    payload_dir.mkdir()
    payload = payload_dir / "bad.json"
    payload.write_text(
        json.dumps(
            {
                "prototype": {"id": "2D Деталь"},
                "document": {"properties": {"Title": "Retry Smoke"}},
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    matrix = tmp_path / "previous_matrix.json"
    matrix.write_text(json.dumps({"rows": [{"ok": False, "payload_path": str(payload)}]}, ensure_ascii=False), encoding="utf-8")
    out = tmp_path / "retry"

    result = _cli("document-factory-batch", "--failed-matrix", str(matrix), "--dry-run", "--output-dir", str(out))

    assert result["ok"] is True
    assert result["selection"] == "failed_matrix"
    assert result["summary"]["selected"] == 1
    assert result["summary"]["buckets"]["passed"] == 1


def test_cli_document_factory_batch_audit_open_only_dry_run(tmp_path):
    payload_dir = tmp_path / "payloads"
    payload_dir.mkdir()
    payload = payload_dir / "audit.json"
    payload.write_text(
        json.dumps(
            {
                "prototype": {"id": "2D Деталь"},
                "document": {"properties": {"Title": "Audit Smoke"}},
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    out = tmp_path / "audit"

    result = _cli("document-factory-batch", "--payload-dir", str(payload_dir), "--audit-open-only", "--dry-run", "--output-dir", str(out))

    assert result["ok"] is True
    assert result["audit_open_only"] is True
    assert result["rows"][0]["stage"] == "audit_dry_run"
    assert result["rows"][0]["audit_open_only"] is True


def test_cli_ui_plugin_probe_compile_only():
    result = _cli("ui-plugin-probe", "--compile-only", "--timeout-sec", "60", timeout=120)

    assert result["ok"] is True
    assert result["stage"] == "compile"
    assert result["compile"]["ok"] is True
    assert Path(result["source_path"]).exists()
    assert Path(result["dll_path"]).exists()
