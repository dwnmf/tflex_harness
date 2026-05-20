from tflex_harness.diagnostics import check_docs_repo, check_dotnet, check_tflex_dlls, get_environment


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
