import pytest

from tflex_harness.recipes import run_recipe


@pytest.mark.integration
def test_run_helper_environment_probe_recipe_live():
    result = run_recipe("helper_environment_probe", timeout_sec=90)

    assert result["ok"] is True, result
    assert result["recipe"] == "helper_environment_probe"
    assert result["recipe_info"]["helpers"] == ["all"]
    assert "easy.init=True" in result["stdout"]
    assert "helperEnvironmentProbe=True" in result["stdout"]
    assert "easy.session=False" in result["stdout"]
    assert len(result["helper_sources"]) == 8


@pytest.mark.integration
def test_run_helper_simple_extrusion_recipe_live():
    result = run_recipe("helper_simple_extrusion", timeout_sec=120)

    assert result["ok"] is True, result
    assert result["recipe"] == "helper_simple_extrusion"
    assert "endChanges=OK" in result["stdout"]
    assert "operations=1" in result["stdout"]
    assert "helper_cylinder20x8.bboxSpanMm=20,20,8" in result["stdout"]
    assert "easy.grbSaved=True" in result["stdout"]
    assert any(item["relative_path"] == "artifacts/helper_simple_extrusion.grb" and item["size"] > 0 for item in result["artifacts"]), result


@pytest.mark.integration
def test_run_helper_step_export_recipe_live():
    result = run_recipe("helper_step_export", timeout_sec=120)

    assert result["ok"] is True, result
    assert result["recipe"] == "helper_step_export"
    assert "endChanges=OK" in result["stdout"]
    assert "helper_cylinder20x8.bboxSpanMm=20,20,8" in result["stdout"]
    assert "easy.stepSaved=True" in result["stdout"]
    assert any(item["relative_path"] == "artifacts/helper_simple.step" and item["size"] > 0 for item in result["artifacts"]), result


@pytest.mark.integration
def test_run_helper_planetary_static_assembly_recipe_live():
    result = run_recipe("helper_planetary_static_assembly", timeout_sec=180)

    assert result["ok"] is True, result
    assert result["recipe"] == "helper_planetary_static_assembly"
    assert "endChanges=OK" in result["stdout"]
    assert "operations=9" in result["stdout"]
    assert "sun_profile_24t_bore10_clearanced.teeth=24" in result["stdout"]
    assert "ring_profile_60t_od140_clearanced.teeth=60" in result["stdout"]
    assert "planet_profile_18t_1_clearanced.teeth=18" in result["stdout"]
    assert "carrier_plate_d105_z_minus5_minus1_clearanced.bboxSpanMm=105,105,4" in result["stdout"]
    assert "pin_1_d6_h14_clearanced.bboxSpanMm=6,6,14" in result["stdout"]
    assert "mesh.sunRadialClearanceMm=0.5" in result["stdout"]
    assert "mesh.ringRadialClearanceMm=0.5" in result["stdout"]
    assert "contractFailCode=0" in result["stdout"]
    assert "easy.grbSaved=True" in result["stdout"]
    assert "easy.stepSaved=True" in result["stdout"]
    assert any(item["relative_path"] == "artifacts/helper_planetary_static_assembly.grb" and item["size"] > 0 for item in result["artifacts"]), result
    assert any(item["relative_path"] == "artifacts/helper_planetary_static_assembly.step" and item["size"] > 0 for item in result["artifacts"]), result
