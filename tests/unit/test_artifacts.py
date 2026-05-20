import json
from dataclasses import dataclass
from pathlib import Path

import pytest

from tflex_harness.artifacts import ArtifactStore, json_default, slugify
from tflex_harness.config import HarnessConfig


def _config(tmp_path: Path) -> HarnessConfig:
    return HarnessConfig(
        repo_dir=tmp_path,
        docs_dir=tmp_path / "docs",
        tflex_install_dir=tmp_path / "tflex",
        tflex_program_dir=tmp_path / "tflex" / "Program",
        runner_dir=tmp_path / "runner" / "TFlexRunner",
        artifacts_dir=tmp_path / "artifacts",
        logs_dir=tmp_path / "logs",
    )


def test_slugify_creates_short_safe_names():
    assert slugify(" live test: create / document ") == "live_test_create_document"
    assert slugify("///") == "run"
    assert len(slugify("x" * 200)) == 80


def test_artifact_store_creates_run_and_tflex_doc_dirs(tmp_path):
    store = ArtifactStore(_config(tmp_path))

    run_dir = store.create_run_dir("sample run")
    docs_dir = store.create_tflex_doc_dir("sample doc")

    assert run_dir.parent == tmp_path / "artifacts" / "runs"
    assert (run_dir / "artifacts").is_dir()
    assert docs_dir.parent == tmp_path / "artifacts" / "tflex_docs"


def test_artifact_store_writes_json_and_text(tmp_path):
    store = ArtifactStore(_config(tmp_path))
    run_dir = store.create_run_dir("write files")

    store.write_text(run_dir / "probe.txt", "hello")
    store.write_json(run_dir / "probe.json", {"path": Path("a/b")})

    assert (run_dir / "probe.txt").read_text(encoding="utf-8") == "hello"
    assert json.loads((run_dir / "probe.json").read_text(encoding="utf-8")) == {"path": str(Path("a/b"))}


@dataclass
class _Payload:
    value: int


def test_json_default_serializes_paths_and_dataclasses():
    assert json_default(Path("a/b")) == str(Path("a/b"))
    assert json_default(_Payload(7)) == {"value": 7}
    with pytest.raises(TypeError):
        json_default(object())
