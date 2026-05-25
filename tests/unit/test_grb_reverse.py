import copy
from pathlib import Path

from tflex_harness.grb_reverse import emit_parametric_csharp, load_evidence, recognize_semantic_model, write_semantic_outputs


FIXTURE = Path("agent_workspace/snippets/grb_reverse_planetary/model_evidence_with_contours.json")


def test_recognize_planetary_evidence_semantics():
    semantic = recognize_semantic_model(load_evidence(FIXTURE))

    assert semantic["operation_count"] == 9
    kinds = [item["kind"] for item in semantic["operations"]]
    assert kinds == [
        "external_trapezoid_gear_with_bore",
        "internal_trapezoid_gear_ring",
        "circle_extrusion",
        "external_trapezoid_gear",
        "circle_extrusion",
        "external_trapezoid_gear",
        "circle_extrusion",
        "external_trapezoid_gear",
        "circle_extrusion",
    ]
    sun = semantic["operations"][0]
    assert sun["teeth"] == 24
    assert sun["root_dia_mm"] == 42
    assert sun["outer_dia_mm"] == 54
    assert sun["bore_dia_mm"] == 10
    ring = semantic["operations"][1]
    assert ring["teeth"] == 60
    assert ring["outer_dia_mm"] == 140
    assert ring["internal_root_dia_mm"] == 126
    assert ring["tooth_tip_dia_mm"] == 114
    assert semantic["operations"][3]["center_mm"] == [42, 0]


def test_recognize_planetary_evidence_blind_without_names():
    evidence = copy.deepcopy(load_evidence(FIXTURE))
    for index, operation in enumerate(evidence["operations"]):
        operation["name"] = f"Op_{index}"

    semantic = recognize_semantic_model(evidence)

    assert [item["kind"] for item in semantic["operations"]] == [
        "external_trapezoid_gear_with_bore",
        "internal_trapezoid_gear_ring",
        "circle_extrusion",
        "external_trapezoid_gear",
        "circle_extrusion",
        "external_trapezoid_gear",
        "circle_extrusion",
        "external_trapezoid_gear",
        "circle_extrusion",
    ]
    assert semantic["operations"][0]["teeth"] == 24
    assert semantic["operations"][1]["teeth"] == 60
    assert semantic["operations"][3]["teeth"] == 18
    assert semantic["operations"][0]["source_name"] == "Op_0"


def test_emit_parametric_csharp_uses_gear_helpers():
    semantic = recognize_semantic_model(load_evidence(FIXTURE))
    code = emit_parametric_csharp(semantic)

    assert "EasyGears.ExternalTrapezoidGearWithBoreAt" in code
    assert "EasyGears.InternalTrapezoidGearRingAt" in code
    assert "EasyGears.ExternalTrapezoidGearAt" in code
    assert "EasyGears.CircleAt" in code
    assert "new double" not in code


def test_write_semantic_outputs(tmp_path):
    result = write_semantic_outputs(FIXTURE, tmp_path)

    assert result["ok"] is True
    assert result["recognized_count"] == 9
    assert (tmp_path / "semantic_model.json").exists()
    assert (tmp_path / "parametric_candidate.cs").exists()
