import json

import pytest

from tflex_harness.workspace import save_snippet_candidate, validate_workspace_name


def test_save_snippet_candidate_writes_review_files(tmp_path, monkeypatch):
    from tflex_harness import config as config_module

    monkeypatch.setenv("TFLEX_ARTIFACTS_DIR", str(tmp_path / "artifacts"))
    cfg = config_module.HarnessConfig(
        repo_dir=tmp_path,
        docs_dir=tmp_path / "docs",
        tflex_install_dir=tmp_path / "T-FLEX CAD 17",
        tflex_program_dir=tmp_path / "T-FLEX CAD 17" / "Program",
        artifacts_dir=tmp_path / "artifacts",
        logs_dir=tmp_path / "logs",
        runner_dir=tmp_path / "runner" / "TFlexRunner",
    )
    (tmp_path / "agent_workspace" / "snippets").mkdir(parents=True)

    result = save_snippet_candidate(
        "hello_probe",
        code="public class Program { public static int Main(){ return 0; } }",
        markdown="# Hello Probe\n\nStatus: candidate.",
        metadata={"docs": ["symbols.jsonl"]},
        config=cfg,
    )

    assert result["ok"] is True
    assert (tmp_path / "agent_workspace" / "snippets" / "hello_probe" / "candidate.cs").exists()
    assert (tmp_path / "agent_workspace" / "snippets" / "hello_probe" / "README.md").read_text(encoding="utf-8").startswith("# Hello Probe")
    metadata = json.loads((tmp_path / "agent_workspace" / "snippets" / "hello_probe" / "metadata.json").read_text(encoding="utf-8"))
    assert metadata["status"] == "candidate"
    assert metadata["metadata"]["docs"] == ["symbols.jsonl"]


def test_workspace_name_validation_rejects_paths():
    assert validate_workspace_name("abc_123") == "abc_123"
    with pytest.raises(ValueError):
        validate_workspace_name("../escape")
    with pytest.raises(ValueError):
        validate_workspace_name("Upper")
