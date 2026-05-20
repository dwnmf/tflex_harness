from tflex_harness.diagnostics import check_docs_repo, check_dotnet, check_tflex_dlls, get_environment, get_live_environment_blockers


def test_environment_reports_docs_and_compiler():
    env = get_environment()
    assert env["docs"]["symbols_jsonl"] is True
    assert env["docs"]["manifest"]["symbol_count"] > 10000
    assert env["tools"]["csc"]["available"] is True
    assert env["runner"]["project_exists"] is True
    assert env["runner"]["build_script_exists"] is True
    assert env["runner"]["executable_exists"] is True
    assert env["runner"]["build_ok"] is True
    assert env["runner"]["env_probe_ok"] is True


def test_diagnostics_helpers_report_goal_contracts():
    dlls = check_tflex_dlls()
    docs = check_docs_repo()
    dotnet = check_dotnet()

    assert dlls["TFlexAPI.dll"]["exists"] is True
    assert dlls["TFlexAPI3D.dll"]["exists"] is True
    assert docs["symbols_jsonl"] is True
    assert docs["chm_pages_jsonl"] is True
    assert docs["types_dir"] is True
    assert docs["manifest"]["assemblies"]["TFlexAPI"] > 0
    assert "available" in dotnet


def test_live_environment_blockers_are_explicit_for_missing_components():
    environment = {
        "tflex_install_dir": {"path": "C:/missing/T-FLEX CAD 17", "exists": False},
        "tflex_program_dir": {"path": "C:/missing/T-FLEX CAD 17/Program", "exists": False},
        "dlls": {"TFlexAPI.dll": {"path": "C:/missing/TFlexAPI.dll", "exists": False}},
        "tools": {"csc": {"available": False, "path": None}},
        "runner": {
            "project_path": "runner/TFlexRunner/TFlexRunner.csproj",
            "project_exists": True,
            "build_script": "runner/TFlexRunner/build.ps1",
            "build_script_exists": True,
            "build_ok": False,
            "error": "test runner unavailable",
        },
    }

    blockers = get_live_environment_blockers(environment)

    assert "T-FLEX CAD 17 install dir missing: C:/missing/T-FLEX CAD 17" in blockers
    assert "T-FLEX CAD 17 program dir missing: C:/missing/T-FLEX CAD 17/Program" in blockers
    assert "T-FLEX DLL missing: C:/missing/TFlexAPI.dll" in blockers
    assert "csc.exe not found" in blockers
    assert "runner unavailable: test runner unavailable" in blockers
