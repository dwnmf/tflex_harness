from tflex_harness.diagnostics import get_environment


def test_environment_reports_docs_and_compiler():
    env = get_environment()
    assert env["docs"]["symbols_jsonl"] is True
    assert env["tools"]["csc"]["available"] is True
    assert env["runner"]["project_exists"] is True
    assert env["runner"]["build_script_exists"] is True
    assert env["runner"]["executable_exists"] is True
    assert env["runner"]["build_ok"] is True
    assert env["runner"]["env_probe_ok"] is True
