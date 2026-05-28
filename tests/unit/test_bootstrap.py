import os
from pathlib import Path

from tflex_harness import bootstrap as bootstrap_module
from tflex_harness.config import HarnessConfig


def _cfg(tmp_path: Path) -> HarnessConfig:
    repo = tmp_path / "tflex_harness"
    repo.mkdir()
    docs = tmp_path / "tflex_api"
    docs.mkdir()
    return HarnessConfig(
        repo_dir=repo,
        docs_dir=docs,
        tflex_install_dir=tmp_path / "T-FLEX CAD 17",
        tflex_program_dir=tmp_path / "T-FLEX CAD 17" / "Program",
        runner_dir=repo / "runner" / "TFlexRunner",
        artifacts_dir=repo / "artifacts",
        logs_dir=repo / "logs",
    )


def test_bootstrap_full_enables_first_install_defaults(monkeypatch, tmp_path):
    cfg = _cfg(tmp_path)
    monkeypatch.setattr(bootstrap_module, "load_config", lambda repo_dir=None: cfg)
    monkeypatch.setattr(
        bootstrap_module,
        "_set_user_env",
        lambda name, value: {"ok": True, "name": name, "value": str(value)},
    )
    monkeypatch.setattr(
        bootstrap_module,
        "_register_codex_skill",
        lambda repo_dir, *, symlink=False: {"ok": True, "mode": "copy", "source": str(repo_dir / "SKILL.md")},
    )
    monkeypatch.setattr(
        bootstrap_module,
        "check_docs_repo",
        lambda cfg: {"symbols_jsonl": True, "chm_pages_jsonl": True, "types_dir": True},
    )
    monkeypatch.setattr(
        bootstrap_module,
        "get_install_doctor",
        lambda config=None: {"ok": True, "blockers": [], "score": {"passed": 10, "total": 10}},
    )

    result = bootstrap_module.bootstrap(full=True)

    assert result["ok"] is True
    assert result["full"] is True
    assert result["persist_env"] is True
    assert [item["name"] for item in result["env"]] == ["TFLEX_HARNESS_REPO_DIR", "TFLEX_API_DOCS_DIR"]
    assert result["skill"]["ok"] is True
    assert result["checks"]["doctor"]["ok"] is True
    assert "restart terminal after --persist-env" in result["next"]
    assert "bootstrap --full already ran install readiness checks" in result["next"]
    assert any("run-csharp --mode compile_only" in step for step in result["next"])


def test_bootstrap_docs_dir_updates_current_process_env(monkeypatch, tmp_path):
    cfg = _cfg(tmp_path)
    custom_docs = tmp_path / "custom_tflex_api"
    custom_docs.mkdir()
    monkeypatch.setattr(bootstrap_module, "load_config", lambda repo_dir=None: cfg)
    monkeypatch.setattr(
        bootstrap_module,
        "_set_user_env",
        lambda name, value: {"ok": True, "name": name, "value": str(value)},
    )
    monkeypatch.setattr(
        bootstrap_module,
        "_register_codex_skill",
        lambda repo_dir, *, symlink=False: {"ok": True, "mode": "copy", "source": str(repo_dir / "SKILL.md")},
    )
    monkeypatch.setattr(
        bootstrap_module,
        "check_docs_repo",
        lambda cfg: {"symbols_jsonl": True, "chm_pages_jsonl": True, "types_dir": True},
    )
    monkeypatch.setattr(
        bootstrap_module,
        "get_install_doctor",
        lambda config=None: {"ok": True, "blockers": [], "score": {"passed": 10, "total": 10}},
    )

    result = bootstrap_module.bootstrap(docs_dir=str(custom_docs), full=True)

    assert result["docs_dir"] == str(custom_docs.resolve())
    assert os.environ["TFLEX_API_DOCS_DIR"] == str(custom_docs.resolve())
