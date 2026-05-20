import pytest

from tflex_harness.artifacts import ArtifactStore
from tflex_harness.config import load_config
from tflex_harness.runner import run_csharp_snippet


@pytest.mark.integration
def test_create_simple_2d_line_save_close_live():
    cfg = load_config()
    doc_dir = ArtifactStore(cfg).create_tflex_doc_dir("integration_create_simple_2d_line")
    output_file = doc_dir / "simple_2d_line.grb"
    recipe = cfg.repo_dir / "agent_workspace" / "recipes" / "create_simple_2d_line.cs"
    code = recipe.read_text(encoding="utf-8")

    result = run_csharp_snippet(
        code,
        mode="run",
        timeout_sec=60,
        artifact_prefix="integration_create_simple_2d_line",
        environment={"TFLEX_RECIPE_OUTPUT_FILE": str(output_file)},
    )

    assert result["ok"] is True, result
    assert "init=True" in result["stdout"]
    assert "docNull=False" in result["stdout"]
    assert "endChanges=OK" in result["stdout"]
    assert "n1=10,10" in result["stdout"]
    assert "n2=50,10" in result["stdout"]
    assert "lineType=ThroughNodes" in result["stdout"]
    assert "object2dType=TFlex.Model.Model2D.FreeNode" in result["stdout"]
    assert "object2dType=TFlex.Model.Model2D.LineConstruction" in result["stdout"]
    assert "objects2d=3" in result["stdout"]
    assert "saved=True" in result["stdout"]
    assert "exists=True" in result["stdout"]
    assert "session=False" in result["stdout"]
    assert output_file.exists()
    assert output_file.stat().st_size > 0
