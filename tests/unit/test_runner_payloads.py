import json
from pathlib import Path

from tflex_harness.config import HarnessConfig
from tflex_harness.runner import parse_csc_diagnostics, write_run_artifacts


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
    cfg = HarnessConfig(
        repo_dir=tmp_path,
        docs_dir=tmp_path / "docs",
        tflex_install_dir=tmp_path / "tflex",
        tflex_program_dir=tmp_path / "tflex" / "Program",
        runner_dir=tmp_path / "runner" / "TFlexRunner",
        artifacts_dir=tmp_path / "artifacts",
        logs_dir=tmp_path / "logs",
    )
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
