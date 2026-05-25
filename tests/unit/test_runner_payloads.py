import json
from pathlib import Path

from tflex_harness.config import HarnessConfig
from tflex_harness import runner as runner_module
from tflex_harness.runner import CompileCache, RunStore, SnippetRunner, parse_csc_diagnostics, resolve_csharp_helpers, run_csharp_snippet, write_run_artifacts


def _config(tmp_path):
    return HarnessConfig(
        repo_dir=tmp_path,
        docs_dir=tmp_path / "docs",
        tflex_install_dir=tmp_path / "tflex",
        tflex_program_dir=tmp_path / "tflex" / "Program",
        runner_dir=tmp_path / "runner" / "TFlexRunner",
        artifacts_dir=tmp_path / "artifacts",
        logs_dir=tmp_path / "logs",
    )


def test_parse_csc_diagnostics():
    text = r"C:\tmp\Snippet.cs(7,13): error CS0246: The type or namespace name 'Foo' could not be found"
    diagnostics = parse_csc_diagnostics(text)
    assert diagnostics == [{
        "file": r"C:\tmp\Snippet.cs",
        "line": 7,
        "column": 13,
        "severity": "error",
        "code": "CS0246",
        "message": "The type or namespace name 'Foo' could not be found",
    }]


def test_write_run_artifacts_creates_reproducible_payload(tmp_path):
    cfg = _config(tmp_path)
    request = {
        "artifact_prefix": "payload test",
        "mode": "run",
        "code": "public class Program {}",
    }
    result = {
        "ok": True,
        "stage": "run",
        "stdout": "out",
        "stderr": "",
        "build_output": "build",
    }

    run_dir = write_run_artifacts(request, result, config=cfg)

    assert run_dir.parent == tmp_path / "artifacts" / "runs"
    assert (run_dir / "request.json").exists()
    assert (run_dir / "snippet.cs").read_text(encoding="utf-8") == request["code"]
    assert (run_dir / "stdout.txt").read_text(encoding="utf-8") == "out"
    assert (run_dir / "stderr.txt").read_text(encoding="utf-8") == ""
    assert (run_dir / "build.log").read_text(encoding="utf-8") == "build"
    assert (run_dir / "run.log").exists()
    persisted = json.loads((run_dir / "result.json").read_text(encoding="utf-8"))
    assert persisted["run_dir"] == str(run_dir)
    assert Path(persisted["snippet_path"]) == run_dir / "snippet.cs"


def test_run_csharp_snippet_rejects_invalid_mode(tmp_path):
    cfg = _config(tmp_path)

    result = run_csharp_snippet(
        "public class Program { public static int Main(){ return 0; } }",
        mode="execute",
        references=[],
        artifact_prefix="test_invalid_mode",
        config=cfg,
    )

    assert result["ok"] is False
    assert result["stage"] == "input"
    assert result["error"] == "invalid mode"
    assert result["allowed_modes"] == ["compile_only", "run"]
    assert result["snippet_path"].endswith("snippet.cs")
    assert result["artifacts_dir"].endswith("artifacts")
    events = (cfg.logs_dir / "events.jsonl").read_text(encoding="utf-8").splitlines()
    record = json.loads(events[-1])
    assert record["event"] == "run_csharp_snippet"
    assert record["payload"]["stage"] == "input"
    assert record["payload"]["run_dir"] == result["run_dir"]


def test_resolve_csharp_helpers_expands_sets(tmp_path):
    cfg = _config(tmp_path)
    helper_dir = tmp_path / "src" / "tflex_harness" / "csharp_helpers"
    helper_dir.mkdir(parents=True)
    (helper_dir / "TFlexEasyUnits.cs").write_text("namespace TFlexEasy {}", encoding="utf-8")
    (helper_dir / "TFlexEasyDiagnostics.cs").write_text("namespace TFlexEasy {}", encoding="utf-8")

    helpers, unknown = resolve_csharp_helpers(cfg, ["easy_core"])

    assert unknown == []
    assert [path.name for path in helpers] == ["TFlexEasyUnits.cs", "TFlexEasyDiagnostics.cs"]


def test_resolve_csharp_helpers_expands_easy_gears(tmp_path):
    cfg = _config(tmp_path)
    helper_dir = tmp_path / "src" / "tflex_harness" / "csharp_helpers"
    helper_dir.mkdir(parents=True)
    for name in ["TFlexEasyUnits.cs", "TFlexEasyDiagnostics.cs", "TFlexEasyPlacement.cs", "TFlexEasyGears.cs"]:
        (helper_dir / name).write_text("namespace TFlexEasy {}", encoding="utf-8")

    helpers, unknown = resolve_csharp_helpers(cfg, ["easy_gears"])

    assert unknown == []
    assert [path.name for path in helpers] == [
        "TFlexEasyUnits.cs",
        "TFlexEasyDiagnostics.cs",
        "TFlexEasyPlacement.cs",
        "TFlexEasyGears.cs",
    ]


def test_resolve_csharp_helpers_expands_easy_prototype(tmp_path):
    cfg = _config(tmp_path)
    helper_dir = tmp_path / "src" / "tflex_harness" / "csharp_helpers"
    helper_dir.mkdir(parents=True)
    for name in ["TFlexEasyUnits.cs", "TFlexEasyDiagnostics.cs", "TFlexEasySession.cs", "TFlexEasyPrototype.cs"]:
        (helper_dir / name).write_text("namespace TFlexEasy {}", encoding="utf-8")

    helpers, unknown = resolve_csharp_helpers(cfg, ["easy_prototype"])

    assert unknown == []
    assert [path.name for path in helpers] == [
        "TFlexEasyUnits.cs",
        "TFlexEasyDiagnostics.cs",
        "TFlexEasySession.cs",
        "TFlexEasyPrototype.cs",
    ]


def test_resolve_csharp_helpers_expands_easy_variables(tmp_path):
    cfg = _config(tmp_path)
    helper_dir = tmp_path / "src" / "tflex_harness" / "csharp_helpers"
    helper_dir.mkdir(parents=True)
    for name in ["TFlexEasyUnits.cs", "TFlexEasyDiagnostics.cs", "TFlexEasySession.cs", "TFlexEasyPrototype.cs", "TFlexEasyVariables.cs"]:
        (helper_dir / name).write_text("namespace TFlexEasy {}", encoding="utf-8")

    helpers, unknown = resolve_csharp_helpers(cfg, ["easy_variables"])

    assert unknown == []
    assert [path.name for path in helpers] == [
        "TFlexEasyUnits.cs",
        "TFlexEasyDiagnostics.cs",
        "TFlexEasySession.cs",
        "TFlexEasyPrototype.cs",
        "TFlexEasyVariables.cs",
    ]


def test_compile_cache_key_includes_helper_content(tmp_path):
    cfg = _config(tmp_path)
    csc = tmp_path / "csc.exe"
    csc.write_text("fake", encoding="utf-8")
    ref = tmp_path / "ref.dll"
    ref.write_text("ref", encoding="utf-8")
    helper = tmp_path / "src" / "tflex_harness" / "csharp_helpers" / "TFlexEasyUnits.cs"
    helper.parent.mkdir(parents=True)
    helper.write_text("namespace TFlexEasy { public static class EasyUnits { public static int V = 1; } }", encoding="utf-8")

    cache = CompileCache(cfg)
    first = cache.key("public class Program {}", [ref], csc, [helper])
    helper.write_text("namespace TFlexEasy { public static class EasyUnits { public static int V = 2; } }", encoding="utf-8")
    second = cache.key("public class Program {}", [ref], csc, [helper])

    assert first != second


def test_run_csharp_snippet_rejects_unknown_helpers_before_environment(tmp_path):
    cfg = _config(tmp_path)

    result = run_csharp_snippet(
        "public class Program { public static int Main(){ return 0; } }",
        mode="compile_only",
        references=[],
        helpers=["missing_helper"],
        artifact_prefix="test_unknown_helper",
        config=cfg,
    )

    assert result["ok"] is False
    assert result["stage"] == "input"
    assert result["error"] == "unknown helpers"
    assert result["unknown_helpers"] == ["missing_helper.cs"]


def test_run_csharp_snippet_persists_helper_metadata(tmp_path, monkeypatch):
    cfg = _config(tmp_path)
    helper_dir = tmp_path / "src" / "tflex_harness" / "csharp_helpers"
    helper_dir.mkdir(parents=True)
    (helper_dir / "TFlexEasyUnits.cs").write_text("namespace TFlexEasy { public static class EasyUnits {} }", encoding="utf-8")

    monkeypatch.setattr(runner_module, "find_csc", lambda: None)
    result = run_csharp_snippet(
        "public class Program { public static int Main(){ return 0; } }",
        mode="compile_only",
        references=[],
        helpers=["TFlexEasyUnits"],
        artifact_prefix="test_helper_metadata",
        config=cfg,
    )

    assert result["stage"] == "environment"
    assert result["helper_sources"][0]["name"] == "TFlexEasyUnits.cs"
    copied = Path(result["helper_sources"][0]["copied_path"])
    assert copied.exists()
    assert copied.parent.name == "helpers"
    request = json.loads((Path(result["run_dir"]) / "request.json").read_text(encoding="utf-8"))
    assert request["helpers"] == ["TFlexEasyUnits"]


def test_runner_exposes_internal_architecture_seams(tmp_path):
    cfg = _config(tmp_path)
    runner = SnippetRunner(cfg)

    assert isinstance(runner.run_store, RunStore)
    assert isinstance(runner.compile_cache, CompileCache)

    result = runner.run(
        "public class Program { public static int Main(){ return 0; } }",
        mode="execute",
        references=[],
        artifact_prefix="test_runner_seams",
    )

    assert result["stage"] == "input"
    assert Path(result["run_dir"]).exists()
