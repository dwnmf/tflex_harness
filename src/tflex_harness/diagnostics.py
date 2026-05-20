from __future__ import annotations

import json
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
        "tools": {
            "python": _version_command([shutil.which("python") or "python", "--version"]),
            "dotnet": _version_command([dotnet, "--info"]) if dotnet else {"available": False},
            "csc": {"available": csc is not None, "path": str(csc) if csc else None},
            "msbuild": {"available": msbuild is not None, "path": str(msbuild) if msbuild else None},
        },
        "tflex_process": {"running": bool(processes), "processes": processes},
    }
