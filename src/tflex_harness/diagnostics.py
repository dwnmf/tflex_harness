from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any

from .config import HarnessConfig, load_config

TFLEX_DLLS = [
    "TFlexAPI.dll",
    "TFlexAPI3D.dll",
    "TFlexAPIData.dll",
    "TFlexCommandAPI.dll",
]


def find_csc() -> Path | None:
    found = shutil.which("csc.exe") or shutil.which("csc")
    if found:
        return Path(found)
    windir = os.environ.get("WINDIR") or os.environ.get("SystemRoot")
    if not windir:
        return None
    candidates = sorted((Path(windir) / "Microsoft.NET" / "Framework64").glob(r"v*\csc.exe"), reverse=True)
    return candidates[0] if candidates else None


def find_msbuild() -> Path | None:
    found = shutil.which("MSBuild.exe") or shutil.which("msbuild.exe") or shutil.which("msbuild")
    if found:
        return Path(found)
    env_msbuild = os.environ.get("TFLEX_MSBUILD_EXE")
    if env_msbuild and Path(env_msbuild).exists():
        return Path(env_msbuild)
    program_files_x86 = os.environ.get("ProgramFiles(x86)")
    vswhere = Path(program_files_x86) / "Microsoft Visual Studio" / "Installer" / "vswhere.exe" if program_files_x86 else None
    if vswhere and vswhere.exists():
        proc = subprocess.run(
            [str(vswhere), "-latest", "-products", "*", "-requires", "Microsoft.Component.MSBuild", "-find", r"MSBuild\**\Bin\MSBuild.exe"],
            text=True,
            capture_output=True,
            timeout=15,
        )
        if proc.returncode == 0:
            line = next((l.strip() for l in proc.stdout.splitlines() if l.strip()), None)
            if line:
                return Path(line)
    return None


def _version_command(command: list[str], timeout: int = 15) -> dict[str, Any]:
    try:
        proc = subprocess.run(command, text=True, capture_output=True, timeout=timeout)
        return {"available": proc.returncode == 0, "returncode": proc.returncode, "stdout": proc.stdout.strip(), "stderr": proc.stderr.strip()}
    except Exception as exc:
        return {"available": False, "error": str(exc)}


def check_tflex_dlls(config: HarnessConfig | None = None) -> dict[str, dict[str, Any]]:
    cfg = config or load_config()
    return {name: {"exists": (cfg.tflex_program_dir / name).exists(), "path": str(cfg.tflex_program_dir / name)} for name in TFLEX_DLLS}


def check_dotnet() -> dict[str, Any]:
    dotnet = shutil.which("dotnet")
    if not dotnet:
        return {"available": False, "version": None}
    status = _version_command([dotnet, "--info"])
    version = _version_command([dotnet, "--version"])
    status["path"] = dotnet
    status["version"] = version.get("stdout") if version.get("available") else _dotnet_host_version(status.get("stdout") or "")
    return status


def _dotnet_host_version(info_output: str) -> str | None:
    match = re.search(r"^\s*Version:\s*([^\s]+)\s*$", info_output, flags=re.MULTILINE)
    return match.group(1) if match else None


def check_docs_repo(config: HarnessConfig | None = None) -> dict[str, Any]:
    cfg = config or load_config()
    status: dict[str, Any] = {
        "dir": str(cfg.docs_dir),
        "exists": cfg.docs_dir.exists(),
        "symbols_jsonl": cfg.symbols_jsonl.exists(),
        "chm_pages_jsonl": cfg.chm_pages_jsonl.exists(),
        "types_dir": cfg.types_dir.exists(),
        "manifest_json": cfg.manifest_json.exists(),
    }
    if cfg.manifest_json.exists():
        try:
            manifest = json.loads(cfg.manifest_json.read_text(encoding="utf-8"))
            status["manifest"] = {
                "symbol_count": manifest.get("symbol_count"),
                "type_page_count": manifest.get("type_page_count"),
                "chm_page_count": manifest.get("chm_page_count"),
                "assemblies": manifest.get("assemblies") or {},
            }
        except Exception as exc:
            status["manifest_error"] = str(exc)
    return status


def _runner_environment(cfg: HarnessConfig, csc: Path | None) -> dict[str, Any]:
    project = cfg.runner_dir / "TFlexRunner.csproj"
    build_script = cfg.runner_dir / "build.ps1"
    executable = cfg.runner_dir / "bin" / "csc" / "Debug" / "TFlexRunner.exe"
    status: dict[str, Any] = {
        "project_path": str(project),
        "project_exists": project.exists(),
        "build_script": str(build_script),
        "build_script_exists": build_script.exists(),
        "executable": str(executable),
        "executable_exists": executable.exists(),
        "build_attempted": False,
        "build_ok": False,
        "env_probe_ok": False,
    }
    if not status["project_exists"] or not status["build_script_exists"]:
        status["error"] = "runner project or build script is missing"
        return status
    if not executable.exists() and csc is not None:
        status["build_attempted"] = True
        try:
            build_env = os.environ.copy()
            build_env["CSC_EXE"] = str(csc)
            build_env["TFLEX_PROGRAM_DIR"] = str(cfg.tflex_program_dir)
            build = subprocess.run(
                ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(build_script), "-Configuration", "Debug"],
                cwd=cfg.runner_dir,
                text=True,
                capture_output=True,
                timeout=60,
                env=build_env,
            )
            status["build_returncode"] = build.returncode
            status["build_stdout"] = build.stdout.strip()
            status["build_stderr"] = build.stderr.strip()
        except Exception as exc:
            status["build_error"] = str(exc)
    status["executable_exists"] = executable.exists()
    if not executable.exists():
        if csc is None:
            status["error"] = "csc.exe not found; runner build skipped"
        return status
    env = os.environ.copy()
    env["PATH"] = str(cfg.tflex_program_dir) + os.pathsep + env.get("PATH", "")
    try:
        probe = subprocess.run([str(executable), "env"], cwd=cfg.runner_dir, text=True, capture_output=True, timeout=30, env=env)
        status["env_probe_returncode"] = probe.returncode
        status["env_probe_stdout"] = probe.stdout.strip()
        status["env_probe_stderr"] = probe.stderr.strip()
        if probe.returncode == 0 and probe.stdout.strip():
            try:
                parsed = json.loads(probe.stdout)
                status["env_probe"] = parsed
                status["env_probe_ok"] = parsed.get("ok") is True
            except json.JSONDecodeError as exc:
                status["env_probe_parse_error"] = str(exc)
    except Exception as exc:
        status["env_probe_error"] = str(exc)
    status["build_ok"] = status["executable_exists"] and status["env_probe_ok"]
    return status


def get_environment(config: HarnessConfig | None = None) -> dict[str, Any]:
    cfg = config or load_config()
    csc = find_csc()
    msbuild = find_msbuild()
    processes = []
    try:
        ps = subprocess.run(
            ["powershell", "-NoProfile", "-Command", "Get-Process | Where-Object { $_.ProcessName -like '*TFlex*' -or $_.ProcessName -like '*T-FLEX*' } | Select-Object Id,ProcessName,Path | ConvertTo-Json -Compress"],
            text=True,
            capture_output=True,
            timeout=20,
        )
        if ps.returncode == 0 and ps.stdout.strip():
            parsed = json.loads(ps.stdout)
            processes = parsed if isinstance(parsed, list) else [parsed]
    except Exception:
        processes = []
    pids = [int(proc["Id"]) for proc in processes if isinstance(proc, dict) and proc.get("Id") is not None]
    dotnet = check_dotnet()
    return {
        "tflex_install_dir": {"path": str(cfg.tflex_install_dir), "exists": cfg.tflex_install_dir.exists()},
        "tflex_program_dir": {"path": str(cfg.tflex_program_dir), "exists": cfg.tflex_program_dir.exists()},
        "dlls": check_tflex_dlls(cfg),
        "docs": check_docs_repo(cfg),
        "dotnet": dotnet,
        "runner": _runner_environment(cfg, csc),
        "tools": {
            "python": _version_command([shutil.which("python") or "python", "--version"]),
            "git": _version_command([shutil.which("git") or "git", "--version"]),
            "uv": _version_command([shutil.which("uv") or "uv", "--version"]),
            "dotnet": dotnet,
            "csc": {"available": csc is not None, "path": str(csc) if csc else None},
            "msbuild": {"available": msbuild is not None, "path": str(msbuild) if msbuild else None},
        },
        "tflex_process": {"running": bool(processes), "pids": pids, "processes": processes},
    }


def get_live_environment_blockers(environment: dict[str, Any] | None = None, config: HarnessConfig | None = None) -> list[str]:
    env = environment or get_environment(config)
    blockers: list[str] = []

    if not env["tflex_install_dir"]["exists"]:
        blockers.append(f"T-FLEX CAD 17 install dir missing: {env['tflex_install_dir']['path']}")
    if not env["tflex_program_dir"]["exists"]:
        blockers.append(f"T-FLEX CAD 17 program dir missing: {env['tflex_program_dir']['path']}")

    for status in env["dlls"].values():
        if not status["exists"]:
            blockers.append(f"T-FLEX DLL missing: {status['path']}")

    if not env["tools"]["csc"]["available"]:
        blockers.append("csc.exe not found")

    runner = env["runner"]
    if not runner["project_exists"]:
        blockers.append(f"runner project missing: {runner['project_path']}")
    if not runner["build_script_exists"]:
        blockers.append(f"runner build script missing: {runner['build_script']}")
    if runner["project_exists"] and runner["build_script_exists"] and not runner["build_ok"]:
        detail = runner.get("error") or runner.get("env_probe_error") or runner.get("build_error") or "runner env probe failed"
        blockers.append(f"runner unavailable: {detail}")

    return blockers


def get_install_doctor(environment: dict[str, Any] | None = None, config: HarnessConfig | None = None) -> dict[str, Any]:
    cfg = config or load_config()
    env = environment or get_environment(cfg)
    checks: list[dict[str, Any]] = []

    def add(name: str, ok: bool, message: str, fix: str | None = None, detail: Any = None) -> None:
        item: dict[str, Any] = {"name": name, "ok": ok, "message": message}
        if fix:
            item["fix"] = fix
        if detail is not None:
            item["detail"] = detail
        checks.append(item)

    add(
        "tflex_install_dir",
        bool(env["tflex_install_dir"]["exists"]),
        f"T-FLEX CAD 17 install dir: {env['tflex_install_dir']['path']}",
        f'setx TFLEX_INSTALL_DIR "{env["tflex_install_dir"]["path"]}" or install T-FLEX CAD 17',
    )
    add(
        "tflex_program_dir",
        bool(env["tflex_program_dir"]["exists"]),
        f"T-FLEX CAD 17 Program dir: {env['tflex_program_dir']['path']}",
        f'setx TFLEX_PROGRAM_DIR "{env["tflex_program_dir"]["path"]}"',
    )

    missing_dlls = [status["path"] for status in env["dlls"].values() if not status["exists"]]
    add(
        "tflex_dlls",
        not missing_dlls,
        "T-FLEX API DLLs found" if not missing_dlls else "T-FLEX API DLLs missing",
        f'setx TFLEX_PROGRAM_DIR "{env["tflex_program_dir"]["path"]}" or repair T-FLEX CAD 17 install',
        missing_dlls or None,
    )

    docs = env["docs"]
    docs_ok = bool(docs["exists"] and docs["symbols_jsonl"] and docs["chm_pages_jsonl"] and docs["types_dir"])
    add(
        "tflex_api_docs",
        docs_ok,
        f"T-FLEX API docs: {docs['dir']}",
        f'tflex-harness bootstrap --docs-dir "{docs["dir"]}" --full',
        {
            "exists": docs["exists"],
            "symbols_jsonl": docs["symbols_jsonl"],
            "chm_pages_jsonl": docs["chm_pages_jsonl"],
            "types_dir": docs["types_dir"],
        },
    )

    recipes_dir = cfg.repo_dir / "agent_workspace" / "recipes"
    workspace_ok = bool((cfg.repo_dir / "install.md").exists() and (cfg.repo_dir / "SKILL.md").exists() and recipes_dir.exists())
    add(
        "repo_workspace",
        workspace_ok,
        f"tflex-harness repo workspace: {cfg.repo_dir}",
        f'Clone https://github.com/dwnmf/tflex_harness and setx TFLEX_HARNESS_REPO_DIR "{cfg.repo_dir}"',
        {
            "install_md": (cfg.repo_dir / "install.md").exists(),
            "skill_md": (cfg.repo_dir / "SKILL.md").exists(),
            "recipes_dir": recipes_dir.exists(),
        },
    )

    python_status = env["tools"]["python"]
    add(
        "python",
        bool(python_status["available"]),
        f"Python available: {python_status.get('stdout') or python_status.get('error')}",
        "Install Python 3.11+ and reopen the terminal",
    )
    git_status = env["tools"].get("git") or {"available": False, "stdout": "", "error": "git not checked"}
    add(
        "git",
        bool(git_status["available"]),
        f"git available: {git_status.get('stdout') or git_status.get('error')}",
        "Install git or clone T-FLEX API docs manually and pass --docs-dir",
    )
    uv_status = env["tools"].get("uv") or {"available": False, "stdout": "", "error": "uv not checked"}
    add(
        "uv",
        True,
        f"uv available: {uv_status.get('stdout')}" if uv_status.get("available") else "uv not found; pip fallback is supported",
        "Optional: install uv for the recommended install path, or use py -m pip install -e \".[mcp]\"",
        {"available": bool(uv_status.get("available"))},
    )
    add(
        "dotnet",
        bool(env["tools"]["dotnet"]["available"]),
        f"dotnet available: {env['tools']['dotnet'].get('version')}",
        "Install .NET runtime/build tools if runner build fails",
    )
    add(
        "csc",
        bool(env["tools"]["csc"]["available"]),
        f"csc.exe: {env['tools']['csc'].get('path')}",
        "Install .NET Framework developer tools or Visual Studio Build Tools",
    )

    runner = env["runner"]
    runner_ok = bool(runner["project_exists"] and runner["build_script_exists"] and runner["build_ok"])
    runner_fix = "Run: tflex-harness env; if still failing, check TFLEX_HARNESS_REPO_DIR and csc.exe"
    add(
        "runner",
        runner_ok,
        "runner build/probe ok" if runner_ok else (runner.get("error") or runner.get("env_probe_error") or runner.get("build_error") or "runner unavailable"),
        runner_fix,
        {
            "project_exists": runner["project_exists"],
            "build_script_exists": runner["build_script_exists"],
            "build_ok": runner["build_ok"],
            "env_probe_ok": runner["env_probe_ok"],
        },
    )

    blockers = [item for item in checks if not item["ok"]]
    return {
        "ok": not blockers,
        "score": {"passed": len(checks) - len(blockers), "total": len(checks)},
        "checks": checks,
        "blockers": blockers,
        "next": [
            "fix blockers in order",
            "run: tflex-harness bootstrap --full",
            "run: tflex-harness env",
            "run: tflex-harness recipes",
        ],
        "repo_dir": str(cfg.repo_dir),
        "docs_dir": str(cfg.docs_dir),
    }
