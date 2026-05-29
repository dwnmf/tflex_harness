import subprocess

from tflex_harness import diagnostics


def test_version_command_detaches_stdin(monkeypatch):
    calls = []

    def fake_run(*args, **kwargs):
        calls.append(kwargs)
        return subprocess.CompletedProcess(args[0], 0, stdout="ok\n", stderr="")

    monkeypatch.setattr(diagnostics.subprocess, "run", fake_run)

    result = diagnostics._version_command(["tool", "--version"])

    assert result["available"] is True
    assert calls[0]["stdin"] is subprocess.DEVNULL


def test_get_environment_process_probe_detaches_stdin(monkeypatch, tmp_path):
    calls = []

    class Cfg:
        tflex_install_dir = tmp_path / "tflex"
        tflex_program_dir = tmp_path / "tflex" / "Program"
        docs_dir = tmp_path / "docs"
        symbols_jsonl = tmp_path / "docs" / "llm" / "symbols.jsonl"
        chm_pages_jsonl = tmp_path / "docs" / "llm" / "chm_pages.jsonl"
        types_dir = tmp_path / "docs" / "llm" / "types"
        manifest_json = tmp_path / "docs" / "llm" / "manifest.json"
        runner_dir = tmp_path / "runner"

    def fake_run(*args, **kwargs):
        calls.append(kwargs)
        return subprocess.CompletedProcess(args[0], 0, stdout="[]", stderr="")

    monkeypatch.setattr(diagnostics, "load_config", lambda: Cfg())
    monkeypatch.setattr(diagnostics, "find_csc", lambda: None)
    monkeypatch.setattr(diagnostics, "find_msbuild", lambda: None)
    monkeypatch.setattr(diagnostics, "check_dotnet", lambda: {"available": False})
    monkeypatch.setattr(diagnostics, "check_tflex_dlls", lambda cfg: {})
    monkeypatch.setattr(diagnostics, "check_docs_repo", lambda cfg: {})
    monkeypatch.setattr(diagnostics, "_runner_environment", lambda cfg, csc: {})
    monkeypatch.setattr(diagnostics, "_version_command", lambda command: {"available": True})
    monkeypatch.setattr(diagnostics.subprocess, "run", fake_run)
    monkeypatch.setattr(diagnostics.shutil, "which", lambda name: name)

    diagnostics.get_environment()

    assert calls
    assert calls[0]["stdin"] is subprocess.DEVNULL
