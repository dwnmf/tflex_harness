from __future__ import annotations

import json
import hashlib
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
from .logging_utils import log_event

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


def _reference_payload(refs: list[Path]) -> list[dict[str, Any]]:
    return [
        {
            "name": ref.stem,
            "dll": ref.name,
            "path": str(ref),
            "exists": ref.exists(),
        }
        for ref in refs
    ]


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


def _collect_artifacts(run_dir: Path) -> list[dict[str, Any]]:
    root = run_dir / "artifacts"
    if not root.exists():
        return []
    artifacts: list[dict[str, Any]] = []
    for path in sorted(p for p in root.rglob("*") if p.is_file()):
        try:
            rel = path.relative_to(run_dir)
        except ValueError:
            rel = path
        artifacts.append({
            "path": str(path),
            "relative_path": str(rel).replace("\\", "/"),
            "size": path.stat().st_size,
        })
    return artifacts


def _compile_cache_key(code: str, refs: list[Path], csc: Path) -> str:
    digest = hashlib.sha256()
    digest.update(b"tflex_harness.csc.v1\0")
    digest.update(str(csc).encode("utf-8", errors="replace"))
    digest.update(b"\0/platform:x64\0/target:exe\0")
    digest.update(code.encode("utf-8"))
    for ref in refs:
        stat = ref.stat()
        digest.update(b"\0ref\0")
        digest.update(str(ref.resolve()).encode("utf-8", errors="replace"))
        digest.update(b"\0")
        digest.update(str(stat.st_size).encode("ascii"))
        digest.update(b"\0")
        digest.update(str(stat.st_mtime_ns).encode("ascii"))
    return digest.hexdigest()


def _cache_dir(cfg: HarnessConfig, key: str) -> Path:
    return cfg.artifacts_dir / "build_cache" / key[:2] / key


def _read_runner_project_settings(project: Path) -> dict[str, str | None]:
    settings: dict[str, str | None] = {"target_framework": None, "platform_target": None}
    if not project.exists():
        return settings
    text = project.read_text(encoding="utf-8", errors="ignore")
    for key, tag in (("target_framework", "TargetFrameworkVersion"), ("platform_target", "PlatformTarget")):
        match = re.search(rf"<{tag}>\s*([^<]+?)\s*</{tag}>", text)
        if match:
            settings[key] = match.group(1).strip()
    return settings


def build_runner(timeout_sec: int = 60, config: HarnessConfig | None = None) -> dict[str, Any]:
    cfg = config or load_config()
    csc = find_csc()
    script = cfg.runner_dir / "build.ps1"
    project = cfg.runner_dir / "TFlexRunner.csproj"
    project_settings = _read_runner_project_settings(project)
    executable = cfg.runner_dir / "bin" / "csc" / "Debug" / "TFlexRunner.exe"
    result: dict[str, Any] = {
        "ok": False,
        "stage": "environment",
        "project_path": str(project),
        "project_exists": project.exists(),
        "build_script": str(script),
        "build_script_exists": script.exists(),
        "executable": str(executable),
        **project_settings,
    }
    if csc is None:
        result["error"] = "csc.exe not found"
        return result
    result["csc"] = str(csc)
    if not project.exists() or not script.exists():
        result["error"] = "runner project or build script is missing"
        return result

    env = os.environ.copy()
    env["CSC_EXE"] = str(csc)
    env["TFLEX_PROGRAM_DIR"] = str(cfg.tflex_program_dir)
    started = time.perf_counter()
    try:
        proc = subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(script), "-Configuration", "Debug"],
            cwd=cfg.runner_dir,
            text=True,
            capture_output=True,
            timeout=timeout_sec,
            env=env,
        )
    except subprocess.TimeoutExpired as exc:
        return {
            **result,
            "stage": "timeout",
            "phase": "build",
            "timeout_sec": timeout_sec,
            "duration_ms": int((time.perf_counter() - started) * 1000),
            "stdout": exc.stdout if isinstance(exc.stdout, str) else "",
            "stderr": exc.stderr if isinstance(exc.stderr, str) else "",
            "error": str(exc),
        }

    stdout = proc.stdout or ""
    stderr = proc.stderr or ""
    last_line = next((line.strip() for line in reversed(stdout.splitlines()) if line.strip()), "")
    built_executable = Path(last_line) if last_line else executable
    return {
        **result,
        "ok": proc.returncode == 0 and built_executable.exists(),
        "stage": "build",
        "exit_code": proc.returncode,
        "duration_ms": int((time.perf_counter() - started) * 1000),
        "stdout": stdout,
        "stderr": stderr,
        "executable": str(built_executable),
        "executable_exists": built_executable.exists(),
    }


def write_run_artifacts(request: dict[str, Any], result: dict[str, Any], config: HarnessConfig | None = None) -> Path:
    cfg = config or load_config()
    store = ArtifactStore(cfg)
    run_dir = store.create_run_dir(str(request.get("artifact_prefix") or result.get("stage") or "run"))
    persisted_result = dict(result)
    persisted_result.setdefault("run_dir", str(run_dir))

    store.write_json(run_dir / "request.json", request)
    if "code" in request:
        store.write_text(run_dir / "snippet.cs", str(request["code"]))
        persisted_result.setdefault("snippet_path", str(run_dir / "snippet.cs"))
    if "stdout" in result:
        store.write_text(run_dir / "stdout.txt", str(result.get("stdout") or ""))
        persisted_result.setdefault("stdout_path", str(run_dir / "stdout.txt"))
    if "stderr" in result:
        store.write_text(run_dir / "stderr.txt", str(result.get("stderr") or ""))
        persisted_result.setdefault("stderr_path", str(run_dir / "stderr.txt"))
    if "build_output" in result:
        store.write_text(run_dir / "build.log", str(result.get("build_output") or ""))
        persisted_result.setdefault("build_log", str(run_dir / "build.log"))
    if "stdout" in result or "stderr" in result:
        store.write_text(run_dir / "run.log", f"STDOUT:\n{result.get('stdout') or ''}\nSTDERR:\n{result.get('stderr') or ''}")
        persisted_result.setdefault("run_log", str(run_dir / "run.log"))

    persisted_result.setdefault("artifacts_dir", str(run_dir / "artifacts"))
    persisted_result.setdefault("artifacts", _collect_artifacts(run_dir))
    store.write_json(run_dir / "result.json", persisted_result)
    return run_dir


def _persist_run_result(cfg: HarnessConfig, store: ArtifactStore, run_dir: Path, result: dict[str, Any]) -> None:
    store.write_json(run_dir / "result.json", result)
    try:
        log_event(
            "run_csharp_snippet",
            {
                "ok": result.get("ok"),
                "stage": result.get("stage"),
                "phase": result.get("phase"),
                "exit_code": result.get("exit_code"),
                "run_dir": result.get("run_dir"),
                "snippet_path": result.get("snippet_path"),
                "cache_key": result.get("cache_key"),
                "cache_hit": result.get("cache_hit"),
                "diagnostic_count": len(result.get("diagnostics") or []),
                "artifact_count": len(result.get("artifacts") or []),
            },
            config=cfg,
        )
    except Exception:
        pass


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
    snippet = run_dir / "snippet.cs"
    store.write_text(snippet, code)

    if mode not in {"compile_only", "run"}:
        result = {
            "ok": False,
            "stage": "input",
            "error": "invalid mode",
            "mode": mode,
            "allowed_modes": ["compile_only", "run"],
            "run_dir": str(run_dir),
            "snippet_path": str(snippet),
            "artifacts_dir": str(run_dir / "artifacts"),
            "artifacts": _collect_artifacts(run_dir),
        }
        _persist_run_result(cfg, store, run_dir, result)
        return result

    csc = find_csc()
    if not csc:
        result = {
            "ok": False,
            "stage": "environment",
            "error": "csc.exe not found",
            "run_dir": str(run_dir),
            "snippet_path": str(snippet),
            "artifacts_dir": str(run_dir / "artifacts"),
            "artifacts": _collect_artifacts(run_dir),
        }
        _persist_run_result(cfg, store, run_dir, result)
        return result

    refs = _default_references(cfg, references)
    resolved_references = _reference_payload(refs)
    missing_refs = []
    if references:
        for name in references:
            dll_name = name if name.lower().endswith(".dll") else f"{name}.dll"
            if not (cfg.tflex_program_dir / dll_name).exists():
                missing_refs.append(str(cfg.tflex_program_dir / dll_name))
    if missing_refs:
        result = {
            "ok": False,
            "stage": "environment",
            "error": "missing references",
            "missing_references": missing_refs,
            "resolved_references": resolved_references,
            "run_dir": str(run_dir),
            "snippet_path": str(snippet),
            "artifacts_dir": str(run_dir / "artifacts"),
            "artifacts": _collect_artifacts(run_dir),
        }
        _persist_run_result(cfg, store, run_dir, result)
        return result

    exe = run_dir / "Snippet.exe"
    cache_key = _compile_cache_key(code, refs, csc)
    cache_dir = _cache_dir(cfg, cache_key)
    cache_exe = cache_dir / "Snippet.exe"
    cache_build_log = cache_dir / "build.log"
    started = time.perf_counter()
    cache_hit = cache_exe.exists()
    if cache_hit:
        cache_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(cache_exe, exe)
        build_output = cache_build_log.read_text(encoding="utf-8") if cache_build_log.exists() else ""
        compile_ms = 0
    else:
        cache_dir.mkdir(parents=True, exist_ok=True)
        cache_snippet = cache_dir / "Snippet.cs"
        store.write_text(cache_snippet, code)
        cmd = [
            str(csc),
            "/nologo",
            "/platform:x64",
            "/target:exe",
            f"/out:{cache_exe}",
        ]
        cmd.extend(f"/reference:{ref}" for ref in refs)
        cmd.append(str(cache_snippet))
        try:
            proc = subprocess.run(cmd, text=True, capture_output=True, timeout=timeout_sec)
        except subprocess.TimeoutExpired as exc:
            compile_ms = int((time.perf_counter() - started) * 1000)
            partial_output = ((exc.stdout or "") if isinstance(exc.stdout, str) else "") + ((exc.stderr or "") if isinstance(exc.stderr, str) else "")
            store.write_text(cache_build_log, partial_output)
            store.write_text(run_dir / "build.log", partial_output)
            result = {
                "ok": False,
                "stage": "timeout",
                "phase": "compile",
                "error": str(exc),
                "timeout_sec": timeout_sec,
                "duration_ms": compile_ms,
                "cache_key": cache_key,
                "cache_hit": False,
                "resolved_references": resolved_references,
                "diagnostics": parse_csc_diagnostics(partial_output),
                "stdout": exc.stdout if isinstance(exc.stdout, str) else "",
                "stderr": exc.stderr if isinstance(exc.stderr, str) else "",
                "run_dir": str(run_dir),
                "snippet_path": str(snippet),
                "build_log": str(run_dir / "build.log"),
                "artifacts_dir": str(run_dir / "artifacts"),
                "artifacts": _collect_artifacts(run_dir),
            }
            _persist_run_result(cfg, store, run_dir, result)
            return result
        build_output = (proc.stdout or "") + (proc.stderr or "")
        store.write_text(cache_build_log, build_output)
        store.write_json(
            cache_dir / "metadata.json",
            {
                "cache_key": cache_key,
                "csc": str(csc),
                "references": [str(ref) for ref in refs],
                "platform": "x64",
                "target": "exe",
            },
        )
        if proc.returncode == 0:
            shutil.copy2(cache_exe, exe)
    compile_ms = int((time.perf_counter() - started) * 1000)
    store.write_text(run_dir / "build.log", build_output)
    diagnostics = parse_csc_diagnostics(build_output)
    compile_exit_code = 0 if cache_hit else proc.returncode
    if compile_exit_code != 0:
        result = {
            "ok": False,
            "stage": "compile",
            "exit_code": compile_exit_code,
            "duration_ms": compile_ms,
            "cache_key": cache_key,
            "cache_hit": False,
            "resolved_references": resolved_references,
            "diagnostics": diagnostics,
            "stdout": proc.stdout,
            "stderr": proc.stderr,
            "run_dir": str(run_dir),
            "snippet_path": str(snippet),
            "build_log": str(run_dir / "build.log"),
            "artifacts_dir": str(run_dir / "artifacts"),
            "artifacts": _collect_artifacts(run_dir),
        }
        _persist_run_result(cfg, store, run_dir, result)
        return result

    if mode == "compile_only":
        result = {
            "ok": True,
            "stage": "compile",
            "exit_code": 0,
            "duration_ms": compile_ms,
            "cache_key": cache_key,
            "cache_hit": cache_hit,
            "resolved_references": resolved_references,
            "diagnostics": diagnostics,
            "run_dir": str(run_dir),
            "snippet_path": str(snippet),
            "executable": str(exe),
            "build_log": str(run_dir / "build.log"),
            "artifacts_dir": str(run_dir / "artifacts"),
            "artifacts": _collect_artifacts(run_dir),
        }
        _persist_run_result(cfg, store, run_dir, result)
        return result
    if mode != "run":
        result = {"ok": False, "stage": "request", "error": f"unsupported mode: {mode}", "run_dir": str(run_dir)}
        _persist_run_result(cfg, store, run_dir, result)
        return result

    _copy_runtime_dlls(run_dir, refs)
    started = time.perf_counter()
    try:
        run_env = _runtime_env(cfg)
        run_env["TFLEX_HARNESS_RUN_DIR"] = str(run_dir)
        run_env["TFLEX_HARNESS_ARTIFACTS_DIR"] = str(run_dir / "artifacts")
        if environment:
            run_env.update({str(k): str(v) for k, v in environment.items()})
        run_proc = subprocess.run([str(exe)], cwd=run_dir, text=True, capture_output=True, timeout=timeout_sec, env=run_env)
        run_ms = int((time.perf_counter() - started) * 1000)
        store.write_text(run_dir / "stdout.txt", run_proc.stdout or "")
        store.write_text(run_dir / "stderr.txt", run_proc.stderr or "")
        store.write_text(run_dir / "run.log", f"STDOUT:\n{run_proc.stdout or ''}\nSTDERR:\n{run_proc.stderr or ''}")
        result = {
            "ok": run_proc.returncode == 0,
            "stage": "run",
            "exit_code": run_proc.returncode,
            "duration_ms": compile_ms + run_ms,
            "compile_duration_ms": compile_ms,
            "run_duration_ms": run_ms,
            "cache_key": cache_key,
            "cache_hit": cache_hit,
            "resolved_references": resolved_references,
            "diagnostics": diagnostics,
            "stdout": run_proc.stdout,
            "stderr": run_proc.stderr,
            "run_dir": str(run_dir),
            "snippet_path": str(snippet),
            "executable": str(exe),
            "build_log": str(run_dir / "build.log"),
            "stdout_path": str(run_dir / "stdout.txt"),
            "stderr_path": str(run_dir / "stderr.txt"),
            "run_log": str(run_dir / "run.log"),
            "artifacts_dir": str(run_dir / "artifacts"),
            "artifacts": _collect_artifacts(run_dir),
        }
    except subprocess.TimeoutExpired as exc:
        result = {
            "ok": False,
            "stage": "timeout",
            "phase": "run",
            "error": str(exc),
            "timeout_sec": timeout_sec,
            "compile_duration_ms": compile_ms,
            "cache_key": cache_key,
            "cache_hit": cache_hit,
            "resolved_references": resolved_references,
            "diagnostics": diagnostics,
            "stdout": exc.stdout if isinstance(exc.stdout, str) else "",
            "stderr": exc.stderr if isinstance(exc.stderr, str) else "",
            "run_dir": str(run_dir),
            "snippet_path": str(snippet),
            "executable": str(exe),
            "artifacts_dir": str(run_dir / "artifacts"),
            "artifacts": _collect_artifacts(run_dir),
        }
    _persist_run_result(cfg, store, run_dir, result)
    return result
