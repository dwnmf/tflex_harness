from __future__ import annotations

import json
import os
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
    candidates = sorted(Path(r"C:\Windows\Microsoft.NET\Framework64").glob(r"v*\csc.exe"), reverse=True)
    return candidates[0] if candidates else None


def find_msbuild() -> Path | None:
    found = shutil.which("MSBuild.exe") or shutil.which("msbuild.exe") or shutil.which("msbuild")
    if found:
        return Path(found)
    vswhere = Path(r"C:\Program Files (x86)\Microsoft Visual Studio\Installer\vswhere.exe")
    if vswhere.exists():
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
    common = Path(r"D:\VSBuildTools\MSBuild\Current\Bin\MSBuild.exe")
    return common if common.exists() else None


def _version_command(command: list[str], timeout: int = 15) -> dict[str, Any]:
    try:
        proc = subprocess.run(command, text=True, capture_output=True, timeout=timeout)
        return {"available": proc.returncode == 0, "returncode": proc.returncode, "stdout": proc.stdout.strip(), "stderr": proc.stderr.strip()}
    except Exception as exc:
        return {"available": False, "error": str(exc)}


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
    dotnet = shutil.which("dotnet")
    dlls = {name: {"exists": (cfg.tflex_program_dir / name).exists(), "path": str(cfg.tflex_program_dir / name)} for name in TFLEX_DLLS}
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
    docs = {
        "dir": str(cfg.docs_dir),
        "exists": cfg.docs_dir.exists(),
        "symbols_jsonl": cfg.symbols_jsonl.exists(),
        "chm_pages_jsonl": cfg.chm_pages_jsonl.exists(),
        "types_dir": cfg.types_dir.exists(),
        "manifest_json": cfg.manifest_json.exists(),
    }
    return {
        "tflex_install_dir": {"path": str(cfg.tflex_install_dir), "exists": cfg.tflex_install_dir.exists()},
        "tflex_program_dir": {"path": str(cfg.tflex_program_dir), "exists": cfg.tflex_program_dir.exists()},
        "dlls": dlls,
        "docs": docs,
        "runner": _runner_environment(cfg, csc),
        "tools": {
            "python": _version_command([shutil.which("python") or "python", "--version"]),
            "dotnet": _version_command([dotnet, "--info"]) if dotnet else {"available": False},
            "csc": {"available": csc is not None, "path": str(csc) if csc else None},
            "msbuild": {"available": msbuild is not None, "path": str(msbuild) if msbuild else None},
        },
        "tflex_process": {"running": bool(processes), "processes": processes},
    }
