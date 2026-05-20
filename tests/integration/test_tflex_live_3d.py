import pytest

from tflex_harness.artifacts import ArtifactStore
from tflex_harness.config import load_config
from tflex_harness.runner import run_csharp_snippet


@pytest.mark.integration
def test_create_simple_3d_extrusion_save_close_live():
    cfg = load_config()
    doc_dir = ArtifactStore(cfg).create_tflex_doc_dir("integration_create_simple_3d_extrusion")
    output_file = doc_dir / "simple_3d_extrusion.grb"
    recipe = cfg.repo_dir / "agent_workspace" / "recipes" / "create_simple_3d_extrusion.cs"
    code = recipe.read_text(encoding="utf-8")

    result = run_csharp_snippet(
        code,
        mode="run",
        timeout_sec=90,
        artifact_prefix="integration_create_simple_3d_extrusion",
        environment={"TFLEX_RECIPE_OUTPUT_FILE": str(output_file)},
    )

    assert result["ok"] is True, result
    assert "init=True" in result["stdout"]
    assert "docNull=False" in result["stdout"]
    assert "operationsBefore=0" in result["stdout"]
    assert "endChanges=OK" in result["stdout"]
    assert "operationsAfter=1" in result["stdout"]
    assert "operationType=TFlex.Model.Model3D.ThickenExtrusion" in result["stdout"]
    assert "bodyNull=False" in result["stdout"]
    assert "geometryNull=False" in result["stdout"]
    assert "bboxValid=True" in result["stdout"]
    assert "bboxPositive=True" in result["stdout"]
    assert "bboxSize=" in result["stdout"]
    assert "saved=True" in result["stdout"]
    assert "exists=True" in result["stdout"]
    assert "session=False" in result["stdout"]
    assert output_file.exists()
    assert output_file.stat().st_size > 0
