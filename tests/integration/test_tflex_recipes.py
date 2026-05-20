import pytest

from tflex_harness.recipes import run_recipe


@pytest.mark.integration
def test_run_environment_probe_recipe_live():
    result = run_recipe("environment_probe", timeout_sec=60)
    assert result["ok"] is True, result
    assert result["recipe"] == "environment_probe"
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
