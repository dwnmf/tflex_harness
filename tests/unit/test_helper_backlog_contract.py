import re

from tflex_harness.config import load_config
from tflex_harness.recipes import list_recipes


def _source(name: str) -> str:
    cfg = load_config()
    path = cfg.repo_dir / "src" / "tflex_harness" / "csharp_helpers" / name
    return path.read_text(encoding="utf-8")


def _assert_public_methods(source: str, methods: list[str]) -> None:
    for method in methods:
        assert re.search(rf"\bpublic\s+static\b[^\n]+?\b{method}\s*\(", source), method


def test_helper_backlog_goal_api_contracts_exist():
    contracts = {
        "TFlexEasyBoolean.cs": [
            "Unite",
            "Subtract",
            "WithBlend",
            "WithChamfer",
            "AddFirst",
            "AddSecond",
        ],
        "TFlexEasySketchProfiles.cs": [
            "Polygon",
            "Rectangle",
            "RoundedRectangle",
            "Triangle",
            "Slot",
            "Obround",
            "LugProfile",
            "WithHole",
        ],
        "TFlexEasyFeatures.cs": [
            "BasePlate",
            "ClevisLugPair",
            "MountingHolePattern",
            "HorizontalBoreCutter",
            "TriangularLighteningCutout",
            "ReinforcingRib",
            "RoundTransitionBlend",
        ],
        "TFlexEasyEvidence.cs": [
            "PrintOperationSummary",
            "PrintFeatureCount",
            "AssertBbox",
            "AssertSaved",
            "FailIfInvalidBbox",
            "WriteManifest",
        ],
        "TFlexEasyReopen.cs": [
            "SaveCloseReopen3D",
            "VerifyReopened",
            "PrintReopenEvidence",
        ],
        "TFlexEasySolids.cs": [
            "BlockMm",
            "CylinderMm",
            "ExtrudeOn",
            "CutCylinderThrough",
            "NamedCutter",
        ],
        "TFlexEasyWorkplanes.cs": [
            "Top",
            "Front",
            "Left",
            "PrintAxisMapping",
            "AssertKnownMapping",
        ],
        "TFlexEasyAssemblyBuild.cs": [
            "CreatePartWithFragmentLcs",
            "InsertFixedFragment",
            "InsertFloatingFragment",
            "CreateTargetLcs",
            "SavePartAndAssembly",
        ],
        "TFlexEasyMateInspector.cs": [
            "PrintMates",
            "PrintMateGeometryOwners",
            "WriteMateGraph",
            "TryExplainMate",
        ],
        "TFlexEasyNativeMates.cs": [
            "FirstSolidBody",
            "Face",
            "Edge",
            "ConcentricByEdgeAxis",
            "CoincidentByFaceSurface",
            "CoincidentByFacePlane",
            "Create",
        ],
        "TFlexEasyCommandProbe.cs": [
            "ListKnownCommands",
            "TryRunSystemCommand",
            "PrintCommandResult",
        ],
        "TFlexEasyExport.cs": [
            "All",
            "VerifyNonEmpty",
            "ExportManifest",
        ],
    }
    for filename, methods in contracts.items():
        _assert_public_methods(_source(filename), methods)


def test_easy_evidence_pure_helpers_keep_fail_contracts():
    source = _source("TFlexEasyEvidence.cs")

    assert "bool ok = expected == actual;" in source
    assert "bool ok = exists && size > 0;" in source
    assert "return invalid ? code : 0;" in source
    assert 'Replace("\\\\", "\\\\\\\\").Replace("\\"", "\\\\\\"")' in source


def test_helper_backlog_verified_recipes_are_fresh():
    recipes = {recipe["name"]: recipe for recipe in list_recipes()}
    for name in {
        "helper_assembly_build_backlog",
        "helper_command_probe_backlog",
        "helper_evidence_unit_backlog",
        "helper_export_matrix_backlog",
        "helper_modeling_backlog",
        "helper_profile_workplanes_backlog",
        "helper_solid_primitives_backlog",
    }:
        recipe = recipes[name]
        assert recipe["verified"] is True
        assert recipe["freshness"]["status"] == "fresh"
