from pathlib import Path

from tflex_harness.config import load_config


def test_config_defaults_point_to_existing_docs():
    cfg = load_config()
    assert cfg.docs_dir.exists()
    assert cfg.symbols_jsonl.exists()
    assert cfg.chm_pages_jsonl.exists()
    assert cfg.types_dir.exists()


def test_config_supports_goal_runner_project_env(monkeypatch, tmp_path):
    runner_project = tmp_path / "CustomRunner"
    monkeypatch.delenv("TFLEX_RUNNER_DIR", raising=False)
    monkeypatch.setenv("TFLEX_RUNNER_PROJECT", str(runner_project))

    cfg = load_config(repo_dir=Path.cwd())

    assert cfg.runner_dir == runner_project


def test_config_runner_dir_overrides_runner_project(monkeypatch, tmp_path):
    runner_project = tmp_path / "ProjectRunner"
    runner_dir = tmp_path / "DirRunner"
    monkeypatch.setenv("TFLEX_RUNNER_PROJECT", str(runner_project))
    monkeypatch.setenv("TFLEX_RUNNER_DIR", str(runner_dir))

    cfg = load_config(repo_dir=Path.cwd())

    assert cfg.runner_dir == runner_dir
