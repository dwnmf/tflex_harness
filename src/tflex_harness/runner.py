from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import time
from pathlib import Path
from typing import Any

from .artifacts import ArtifactStore
from .config import HarnessConfig, load_config
from .diagnostics import TFLEX_DLLS, find_csc

DIAG_RE = re.compile(r"^(?P<file>.*)\((?P<line>\d+),(?P<column>\d+)\):\s*(?P<severity>error|warning)\s*(?P<code>CS\d+)\s*:\s*(?P<message>.*)$")


def parse_csc_diagnostics(output: str) -> list[dict[str, Any]]:
    diagnostics: list[dict[str, Any]] = []
    for line in output.splitlines():
        match = DIAG_RE.match(line.strip())
        if match:
            item = match.groupdict()
            item["line"] = int(item["line"])
            item["column"] = int(item["column"])
            diagnostics.append(item)
    return diagnostics


def _default_references(cfg: HarnessConfig, selected: list[str] | None) -> list[Path]:
    names = TFLEX_DLLS if selected is None else selected
    resolved: list[Path] = []
    for name in names:
        dll_name = name if name.lower().endswith(".dll") else f"{name}.dll"
        path = cfg.tflex_program_dir / dll_name
        if path.exists():
            resolved.append(path)
    return resolved


def _copy_runtime_dlls(run_dir: Path, references: list[Path]) -> None:
    for ref in references:
        target = run_dir / ref.name
        if not target.exists():
            shutil.copy2(ref, target)


def _runtime_env(cfg: HarnessConfig) -> dict[str, str]:
    env = os.environ.copy()
    program = str(cfg.tflex_program_dir)
    env["PATH"] = program + os.pathsep + env.get("PATH", "")
    return env


def run_csharp_snippet(
    code: str,
    mode: str = "run",
    timeout_sec: int = 30,
    references: list[str] | None = None,
    artifact_prefix: str = "snippet",
    environment: dict[str, str] | None = None,
    config: HarnessConfig | None = None,
) -> dict[str, Any]:
    cfg = config or load_config()
    store = ArtifactStore(cfg)
    run_dir = store.create_run_dir(artifact_prefix)
    request = {"mode": mode, "timeout_sec": timeout_sec, "references": references, "artifact_prefix": artifact_prefix, "environment": environment or {}}
    store.write_json(run_dir / "request.json", request)
    snippet = run_dir / "Snippet.cs"
    store.write_text(snippet, code)

    csc = find_csc()
    if not csc:
        result = {"ok": False, "stage": "environment", "error": "csc.exe not found", "run_dir": str(run_dir)}
        store.write_json(run_dir / "result.json", result)
        return result

    refs = _default_references(cfg, references)
    missing_refs = []
    if references:
        for name in references:
            dll_name = name if name.lower().endswith(".dll") else f"{name}.dll"
            if not (cfg.tflex_program_dir / dll_name).exists():
                missing_refs.append(str(cfg.tflex_program_dir / dll_name))
    if missing_refs:
        result = {"ok": False, "stage": "environment", "error": "missing references", "missing_references": missing_refs, "run_dir": str(run_dir)}
        store.write_json(run_dir / "result.json", result)
        return result

    exe = run_dir / "Snippet.exe"
    cmd = [
        str(csc),
        "/nologo",
        "/platform:x64",
        "/target:exe",
        f"/out:{exe}",
    ]
    cmd.extend(f"/reference:{ref}" for ref in refs)
    cmd.append(str(snippet))
    started = time.perf_counter()
    proc = subprocess.run(cmd, text=True, capture_output=True, timeout=timeout_sec)
    compile_ms = int((time.perf_counter() - started) * 1000)
    build_output = (proc.stdout or "") + (proc.stderr or "")
    store.write_text(run_dir / "build.log", build_output)
    diagnostics = parse_csc_diagnostics(build_output)
    if proc.returncode != 0:
        result = {
            "ok": False,
            "stage": "compile",
            "exit_code": proc.returncode,
            "duration_ms": compile_ms,
            "diagnostics": diagnostics,
            "stdout": proc.stdout,
            "stderr": proc.stderr,
            "run_dir": str(run_dir),
            "snippet_path": str(snippet),
            "build_log": str(run_dir / "build.log"),
        }
        store.write_json(run_dir / "result.json", result)
        return result

    if mode == "compile_only":
        result = {
            "ok": True,
            "stage": "compile",
            "exit_code": 0,
            "duration_ms": compile_ms,
            "diagnostics": diagnostics,
            "run_dir": str(run_dir),
            "snippet_path": str(snippet),
            "executable": str(exe),
            "build_log": str(run_dir / "build.log"),
        }
        store.write_json(run_dir / "result.json", result)
        return result
    if mode != "run":
        result = {"ok": False, "stage": "request", "error": f"unsupported mode: {mode}", "run_dir": str(run_dir)}
        store.write_json(run_dir / "result.json", result)
        return result

    _copy_runtime_dlls(run_dir, refs)
    started = time.perf_counter()
    try:
        run_env = _runtime_env(cfg)
        if environment:
            run_env.update({str(k): str(v) for k, v in environment.items()})
        run_proc = subprocess.run([str(exe)], cwd=run_dir, text=True, capture_output=True, timeout=timeout_sec, env=run_env)
        run_ms = int((time.perf_counter() - started) * 1000)
        store.write_text(run_dir / "stdout.txt", run_proc.stdout or "")
        store.write_text(run_dir / "stderr.txt", run_proc.stderr or "")
        result = {
            "ok": run_proc.returncode == 0,
            "stage": "run",
            "exit_code": run_proc.returncode,
            "duration_ms": compile_ms + run_ms,
            "compile_duration_ms": compile_ms,
            "run_duration_ms": run_ms,
            "diagnostics": diagnostics,
            "stdout": run_proc.stdout,
            "stderr": run_proc.stderr,
            "run_dir": str(run_dir),
            "snippet_path": str(snippet),
            "executable": str(exe),
            "build_log": str(run_dir / "build.log"),
            "stdout_path": str(run_dir / "stdout.txt"),
            "stderr_path": str(run_dir / "stderr.txt"),
        }
    except subprocess.TimeoutExpired as exc:
        result = {
            "ok": False,
            "stage": "timeout",
            "error": str(exc),
            "timeout_sec": timeout_sec,
            "diagnostics": diagnostics,
            "run_dir": str(run_dir),
            "snippet_path": str(snippet),
            "executable": str(exe),
        }
    store.write_json(run_dir / "result.json", result)
    return result
