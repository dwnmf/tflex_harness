from pathlib import Path

from tflex_harness.config import HarnessConfig
from tflex_harness.diagnostics import check_docs_repo, check_dotnet, check_tflex_dlls, get_environment, get_install_doctor, get_live_environment_blockers


def test_environment_reports_docs_and_compiler():
    env = get_environment()
    assert env["docs"]["symbols_jsonl"] is True
    assert env["docs"]["manifest"]["symbol_count"] > 10000
    assert "available" in env["dotnet"]
    assert "version" in env["dotnet"]
    assert env["tools"]["dotnet"] == env["dotnet"]
    assert env["tools"]["csc"]["available"] is True
    assert env["runner"]["project_exists"] is True
    assert env["runner"]["build_script_exists"] is True
    assert env["runner"]["executable_exists"] is True
    assert env["runner"]["build_ok"] is True
    assert env["runner"]["env_probe_ok"] is True
    assert isinstance(env["tflex_process"]["pids"], list)


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
    assert "version" in dotnet


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


def test_install_doctor_returns_fix_hints_for_missing_components():
    environment = {
        "tflex_install_dir": {"path": "C:/missing/T-FLEX CAD 17", "exists": False},
        "tflex_program_dir": {"path": "C:/missing/T-FLEX CAD 17/Program", "exists": False},
        "dlls": {"TFlexAPI.dll": {"path": "C:/missing/TFlexAPI.dll", "exists": False}},
        "docs": {
            "dir": "C:/missing/tflex_api",
            "exists": False,
            "symbols_jsonl": False,
            "chm_pages_jsonl": False,
            "types_dir": False,
        },
        "tools": {
            "python": {"available": True, "stdout": "Python 3.11.0"},
            "dotnet": {"available": False, "version": None},
            "csc": {"available": False, "path": None},
        },
        "runner": {
            "project_exists": True,
            "build_script_exists": True,
            "build_ok": False,
            "env_probe_ok": False,
            "error": "test runner unavailable",
        },
    }

    doctor = get_install_doctor(environment)

    assert doctor["ok"] is False
    assert doctor["score"]["total"] == len(doctor["checks"])
    assert all(item.get("fix") for item in doctor["blockers"])
    assert "tflex_api_docs" in {item["name"] for item in doctor["blockers"]}


def test_install_doctor_reports_missing_repo_workspace(tmp_path):
    cfg = HarnessConfig(
        repo_dir=tmp_path / "not_checkout",
        docs_dir=tmp_path / "tflex_api",
        tflex_install_dir=Path("C:/Program Files/T-FLEX CAD 17"),
        tflex_program_dir=Path("C:/Program Files/T-FLEX CAD 17/Program"),
        runner_dir=tmp_path / "not_checkout" / "runner" / "TFlexRunner",
        artifacts_dir=tmp_path / "not_checkout" / "artifacts",
        logs_dir=tmp_path / "not_checkout" / "logs",
    )
    environment = {
        "tflex_install_dir": {"path": str(cfg.tflex_install_dir), "exists": True},
        "tflex_program_dir": {"path": str(cfg.tflex_program_dir), "exists": True},
        "dlls": {"TFlexAPI.dll": {"path": "C:/Program Files/T-FLEX CAD 17/Program/TFlexAPI.dll", "exists": True}},
        "docs": {
            "dir": str(cfg.docs_dir),
            "exists": True,
            "symbols_jsonl": True,
            "chm_pages_jsonl": True,
            "types_dir": True,
        },
        "tools": {
            "python": {"available": True, "stdout": "Python 3.11.0"},
            "git": {"available": True, "stdout": "git version 2"},
            "uv": {"available": False, "error": "uv missing"},
            "dotnet": {"available": True, "version": "8.0"},
            "csc": {"available": True, "path": "csc.exe"},
        },
        "runner": {
            "project_exists": True,
            "build_script_exists": True,
            "build_ok": True,
            "env_probe_ok": True,
        },
    }

    doctor = get_install_doctor(environment, config=cfg)
    blockers = {item["name"]: item for item in doctor["blockers"]}

    assert "repo_workspace" in blockers
    assert "TFLEX_HARNESS_REPO_DIR" in blockers["repo_workspace"]["fix"]
