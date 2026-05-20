from pathlib import Path

import pytest

from tflex_harness.artifacts import ArtifactStore
from tflex_harness.config import load_config
from tflex_harness.runner import run_csharp_snippet


@pytest.mark.integration
def test_create_empty_document_save_close_live():
    cfg = load_config()
    doc_dir = ArtifactStore(cfg).create_tflex_doc_dir("integration_create_empty_document")
    output_file = doc_dir / "empty_document.grb"
    recipe = cfg.repo_dir / "agent_workspace" / "recipes" / "create_empty_document.cs"
    code = recipe.read_text(encoding="utf-8")

    result = run_csharp_snippet(
        code,
        mode="run",
        timeout_sec=60,
        artifact_prefix="integration_create_empty_document",
        environment={"TFLEX_RECIPE_OUTPUT_FILE": str(output_file)},
    )

    assert result["ok"] is True, result
    assert "init=True" in result["stdout"]
    assert "docNull=False" in result["stdout"]
    assert "saved=True" in result["stdout"]
    assert "exists=True" in result["stdout"]
    assert "session=False" in result["stdout"]
    assert output_file.exists()
    assert output_file.stat().st_size > 0
