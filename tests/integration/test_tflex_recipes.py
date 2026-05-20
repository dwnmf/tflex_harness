import pytest

from tflex_harness.recipes import run_recipe


@pytest.mark.integration
def test_run_environment_probe_recipe_live():
    result = run_recipe("environment_probe", timeout_sec=60)
    assert result["ok"] is True, result
    assert result["recipe"] == "environment_probe"
    assert result["recipe_info"]["source_path"].endswith("environment_probe.cs")
    assert result["recipe_info"]["markdown_path"].endswith("environment_probe.md")
    assert result["recipe_info"]["source_exists"] is True
    assert result["recipe_info"]["markdown_exists"] is True
    assert "init=True" in result["stdout"]
    assert "exited=False" in result["stdout"]


@pytest.mark.integration
def test_run_create_empty_document_recipe_live():
    result = run_recipe("create_empty_document", timeout_sec=60)
    assert result["ok"] is True, result
    assert result["recipe"] == "create_empty_document"
    assert "saved=True" in result["stdout"]
    output = result["recipe_artifacts"]["output_file"]
    import pathlib
    path = pathlib.Path(output)
    assert path.exists()
    assert path.stat().st_size > 0


@pytest.mark.integration
def test_run_save_document_as_temp_recipe_live():
    result = run_recipe("save_document_as_temp", timeout_sec=60)
    assert result["ok"] is True, result
    assert result["recipe"] == "save_document_as_temp"
    assert "saved=True" in result["stdout"]
    assert "exists=True" in result["stdout"]
    assert "fileNameAfter=" in result["stdout"]
    assert "artifactMarker=" in result["stdout"]
    assert any(item["relative_path"] == "artifacts/saved_document_path.txt" for item in result["artifacts"]), result
    output = result["recipe_artifacts"]["output_file"]
    import pathlib
    path = pathlib.Path(output)
    assert path.exists()
    assert path.stat().st_size > 0


@pytest.mark.integration
def test_run_create_simple_2d_line_recipe_live():
    result = run_recipe("create_simple_2d_line", timeout_sec=60)
    assert result["ok"] is True, result
    assert result["recipe"] == "create_simple_2d_line"
    assert "endChanges=OK" in result["stdout"]
    assert "lineType=ThroughNodes" in result["stdout"]
    assert "objects2d=3" in result["stdout"]
    assert "saved=True" in result["stdout"]
    output = result["recipe_artifacts"]["output_file"]
    import pathlib
    path = pathlib.Path(output)
    assert path.exists()
    assert path.stat().st_size > 0


@pytest.mark.integration
def test_run_create_simple_3d_extrusion_recipe_live():
    result = run_recipe("create_simple_3d_extrusion", timeout_sec=90)
    assert result["ok"] is True, result
    assert result["recipe"] == "create_simple_3d_extrusion"
    assert "endChanges=OK" in result["stdout"]
    assert "operationsAfter=1" in result["stdout"]
    assert "operationType=TFlex.Model.Model3D.ThickenExtrusion" in result["stdout"]
    assert "bodyNull=False" in result["stdout"]
    assert "geometryNull=False" in result["stdout"]
    assert "bboxValid=True" in result["stdout"]
    assert "bboxPositive=True" in result["stdout"]
    assert "saved=True" in result["stdout"]
    output = result["recipe_artifacts"]["output_file"]
    import pathlib
    path = pathlib.Path(output)
    assert path.exists()
    assert path.stat().st_size > 0
