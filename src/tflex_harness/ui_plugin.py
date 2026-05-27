from __future__ import annotations

import json
import os
import subprocess
import time
import uuid
from pathlib import Path
from typing import Any

from .artifacts import ArtifactStore, slugify
from .config import HarnessConfig, load_config
from .diagnostics import find_csc
from .logging_utils import log_event
from .runner import parse_csc_diagnostics


def _render_probe_source(plugin_guid: str) -> str:
    return f"""using System;
using System.Diagnostics;
using System.IO;
using TFlex;

namespace TFlexHarnessUiProbe
{{
  public class Factory : PluginFactory
  {{
    public override Plugin CreateInstance() {{ return new ProbePlugin(this); }}
    public override Guid ID {{ get {{ return new Guid("{{{plugin_guid}}}"); }} }}
    public override string Name {{ get {{ return "T-FLEX Harness UI Probe"; }} }}
    public override bool BeforeAll {{ get {{ return true; }} }}
  }}

  public class ProbePlugin : Plugin
  {{
    public ProbePlugin(Factory f) : base(f) {{ }}

    void Write(string stage)
    {{
      try
      {{
        string path = Environment.GetEnvironmentVariable("TFLEX_HARNESS_UI_PROBE_FILE");
        if (String.IsNullOrWhiteSpace(path)) return;
        string dir = Path.GetDirectoryName(path);
        if (!String.IsNullOrWhiteSpace(dir)) Directory.CreateDirectory(dir);
        File.AppendAllText(path, DateTime.UtcNow.ToString("o") + "|" + stage + "|pid=" + Process.GetCurrentProcess().Id + Environment.NewLine);
      }}
      catch {{ }}
    }}

    protected override void OnInitialize()
    {{
      base.OnInitialize();
      Write("OnInitialize");
    }}

    protected override void OnCreateTools()
    {{
      base.OnCreateTools();
      Write("OnCreateTools");
    }}
  }}
}}
"""


def _compile_probe_plugin(
    source_path: Path,
    dll_path: Path,
    timeout_sec: int,
    config: HarnessConfig,
) -> dict[str, Any]:
    csc = find_csc()
    if csc is None:
        return {"ok": False, "stage": "environment", "error": "csc.exe not found"}

    refs = [
        config.tflex_program_dir / "TFlexAPI.dll",
        config.tflex_program_dir / "TFlexCommandAPI.dll",
    ]
    missing_refs = [str(path) for path in refs if not path.exists()]
    if missing_refs:
        return {
            "ok": False,
            "stage": "environment",
            "error": "missing references",
            "missing_references": missing_refs,
        }

    cmd = [
        str(csc),
        "/nologo",
        "/target:library",
        "/platform:anycpu",
        f"/out:{dll_path}",
        *(f"/reference:{ref}" for ref in refs),
        str(source_path),
    ]
    started = time.perf_counter()
    try:
        proc = subprocess.run(
            cmd,
            text=True,
            encoding="utf-8",
            errors="replace",
            capture_output=True,
            timeout=timeout_sec,
        )
    except subprocess.TimeoutExpired as exc:
        output = ((exc.stdout or "") if isinstance(exc.stdout, str) else "") + ((exc.stderr or "") if isinstance(exc.stderr, str) else "")
        return {
            "ok": False,
            "stage": "timeout",
            "phase": "compile",
            "error": str(exc),
            "timeout_sec": timeout_sec,
            "duration_ms": int((time.perf_counter() - started) * 1000),
            "stdout": exc.stdout if isinstance(exc.stdout, str) else "",
            "stderr": exc.stderr if isinstance(exc.stderr, str) else "",
            "output": output,
            "diagnostics": parse_csc_diagnostics(output),
            "command": cmd,
        }

    output = (proc.stdout or "") + (proc.stderr or "")
    return {
        "ok": proc.returncode == 0 and dll_path.exists(),
        "stage": "compile",
        "phase": "compile",
        "exit_code": proc.returncode,
        "duration_ms": int((time.perf_counter() - started) * 1000),
        "stdout": proc.stdout or "",
        "stderr": proc.stderr or "",
        "output": output,
        "diagnostics": parse_csc_diagnostics(output),
        "command": cmd,
        "dll_exists": dll_path.exists(),
    }


def _append_ini_section(path: Path, section_text: str) -> tuple[bool, bytes | None]:
    existed = path.exists()
    backup = path.read_bytes() if existed else None
    path.parent.mkdir(parents=True, exist_ok=True)
    current = backup or b""
    if current and not current.endswith(b"\n"):
        current += b"\r\n"
    current += section_text.encode("ascii", errors="strict")
    path.write_bytes(current)
    return existed, backup


def _restore_ini(path: Path, existed: bool, backup: bytes | None) -> None:
    if existed:
        if backup is not None:
            path.write_bytes(backup)
    else:
        if path.exists():
            path.unlink(missing_ok=True)


def _registry_candidates() -> list[str]:
    return [
        r"Software\Top Systems\T-FLEX CAD 3D 17\Rus\Applications",
        r"Software\Top Systems\Applications",
        r"Software\WOW6432Node\Top Systems\Applications",
    ]


def _ini_candidates(config: HarnessConfig) -> list[Path]:
    local = Path(os.environ.get("LOCALAPPDATA", ""))
    roaming = Path(os.environ.get("APPDATA", ""))
    return [
        config.tflex_program_dir / "Applications.ini",
        local / "Top Systems" / "T-FLEX CAD 3D 17" / "Rus" / "Applications.ini",
        local / "Top Systems" / "T-FLEX CAD" / "Applications.ini",
        local / "Top Systems" / "T-FLEX CAD 3D 17" / "Rus" / "Profiles" / "[Current]" / "Applications.ini",
        roaming / "Top Systems" / "T-FLEX CAD 3D 17" / "Rus" / "Applications.ini",
        roaming / "Top Systems" / "T-FLEX CAD" / "Applications.ini",
    ]


def _current_tflex_processes() -> list[dict[str, Any]]:
    try:
        proc = subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-Command",
                "Get-Process | Where-Object { $_.ProcessName -like '*TFlex*' -or $_.ProcessName -like '*T-FLEX*' } | Select-Object Id,ProcessName,Path | ConvertTo-Json -Compress",
            ],
            text=True,
            encoding="utf-8",
            errors="replace",
            capture_output=True,
            timeout=20,
        )
        if proc.returncode != 0 or not proc.stdout.strip():
            return []
        parsed = json.loads(proc.stdout)
        rows = parsed if isinstance(parsed, list) else [parsed]
        return [row for row in rows if isinstance(row, dict)]
    except Exception:
        return []


def _launch_tflex_probe(
    config: HarnessConfig,
    evidence_path: Path,
    startup_wait_sec: int,
) -> dict[str, Any]:
    exe = config.tflex_program_dir / "TFlexCad.exe"
    if not exe.exists():
        return {"ok": False, "stage": "environment", "error": f"TFlexCad.exe not found: {exe}"}

    preexisting = _current_tflex_processes()
    preexisting_pids = [int(item["Id"]) for item in preexisting if item.get("Id") is not None]
    env = os.environ.copy()
    env["TFLEX_HARNESS_UI_PROBE_FILE"] = str(evidence_path)
    started = time.perf_counter()
    try:
        proc = subprocess.Popen(
            [str(exe)],
            cwd=config.tflex_program_dir,
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except OSError as exc:
        return {
            "ok": False,
            "stage": "launch",
            "error": str(exc),
            "preexisting_tflex_pids": preexisting_pids,
        }

    loaded = False
    try:
        deadline = time.perf_counter() + max(1, startup_wait_sec)
        while time.perf_counter() < deadline:
            if evidence_path.exists():
                text = evidence_path.read_text(encoding="utf-8", errors="replace")
                if "OnInitialize" in text or "OnCreateTools" in text:
                    loaded = True
                    break
            if proc.poll() is not None:
                break
            time.sleep(0.5)
    finally:
        if proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=4)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait(timeout=4)

    evidence = evidence_path.read_text(encoding="utf-8", errors="replace") if evidence_path.exists() else ""
    return {
        "ok": loaded,
        "stage": "run",
        "loaded": loaded,
        "duration_ms": int((time.perf_counter() - started) * 1000),
        "launched_pid": proc.pid,
        "process_exit_code": proc.returncode,
        "evidence_path": str(evidence_path),
        "evidence_exists": evidence_path.exists(),
        "evidence": evidence,
        "preexisting_tflex_pids": preexisting_pids,
    }


def _attempt_ini_backend(
    backend_id: str,
    ini_path: Path,
    dll_path: Path,
    plugin_guid: str,
    run_dir: Path,
    startup_wait_sec: int,
    config: HarnessConfig,
) -> dict[str, Any]:
    attempt: dict[str, Any] = {
        "backend": backend_id,
        "kind": "ini",
        "ini_path": str(ini_path),
        "dll_path": str(dll_path),
    }
    existed = False
    backup: bytes | None = None
    evidence_path = run_dir / f"evidence_{slugify(backend_id)}.txt"
    try:
        section = (
            f"[{plugin_guid}]\r\n"
            f"Dll={dll_path}\r\n"
            "Name=T-FLEX Harness UI Probe\r\n"
            "Managed=1\r\n"
            "AutoStart=1\r\n\r\n"
        )
        existed, backup = _append_ini_section(ini_path, section)
        attempt["registration_ok"] = True
        attempt["registration_method"] = "ini_append"
        attempt["launch"] = _launch_tflex_probe(config, evidence_path, startup_wait_sec)
        attempt["ok"] = bool(attempt["launch"].get("ok"))
    except Exception as exc:
        attempt["ok"] = False
        attempt["registration_ok"] = False
        attempt["error"] = str(exc)
    finally:
        try:
            _restore_ini(ini_path, existed, backup)
        except Exception as exc:  # pragma: no cover - cleanup best-effort
            attempt["cleanup_error"] = str(exc)
    return attempt


def _attempt_registry_backend(
    backend_id: str,
    registry_path: str,
    dll_path: Path,
    plugin_guid: str,
    run_dir: Path,
    startup_wait_sec: int,
    config: HarnessConfig,
) -> dict[str, Any]:
    attempt: dict[str, Any] = {
        "backend": backend_id,
        "kind": "registry",
        "registry_path": registry_path,
        "dll_path": str(dll_path),
    }
    evidence_path = run_dir / f"evidence_{slugify(backend_id)}.txt"
    unique_key = f"tflex-harness-ui-probe-{slugify(plugin_guid.lower(), max_len=32)}"
    full_subkey = registry_path + "\\" + unique_key
    created = False
    try:
        import winreg

        values = {
            "Autostart": "1",
            "MaxBuild": "17999",
            "Name": "T-FLEX Harness UI Probe",
            "Path": str(dll_path),
            "AnyCPU": "1",
            "Type": "generic",
            "Version": "3D,SE",
            "Product": "CAD",
            "MinBuild": "17001",
            "Language": "Rus",
            "Key": plugin_guid,
            "Managed": "1",
        }
        with winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, full_subkey, 0, winreg.KEY_WRITE) as key:
            for key_name, value in values.items():
                winreg.SetValueEx(key, key_name, 0, winreg.REG_SZ, value)
        created = True
        attempt["registration_ok"] = True
        attempt["registration_method"] = "registry_hkcu"
        attempt["registry_subkey"] = full_subkey
        attempt["launch"] = _launch_tflex_probe(config, evidence_path, startup_wait_sec)
        attempt["ok"] = bool(attempt["launch"].get("ok"))
    except Exception as exc:
        attempt["ok"] = False
        attempt["registration_ok"] = False
        attempt["error"] = str(exc)
    finally:
        if created:
            try:
                import winreg

                winreg.DeleteKey(winreg.HKEY_CURRENT_USER, full_subkey)
            except Exception as exc:  # pragma: no cover - cleanup best-effort
                attempt["cleanup_error"] = str(exc)
    return attempt


def run_ui_plugin_probe(
    timeout_sec: int = 90,
    startup_wait_sec: int = 10,
    compile_only: bool = False,
    config: HarnessConfig | None = None,
) -> dict[str, Any]:
    cfg = config or load_config()
    store = ArtifactStore(cfg)
    run_dir = store.create_run_dir("ui_plugin_probe")
    plugin_guid = str(uuid.uuid4()).upper()
    source_path = run_dir / "HarnessUiProbe.cs"
    dll_path = run_dir / "HarnessUiProbe.dll"
    build_log_path = run_dir / "plugin_build.log"

    source = _render_probe_source(plugin_guid)
    store.write_text(source_path, source)
    compile_result = _compile_probe_plugin(source_path, dll_path, timeout_sec, cfg)
    store.write_text(build_log_path, str(compile_result.get("output") or ""))

    result: dict[str, Any] = {
        "ok": False,
        "stage": "compile",
        "run_dir": str(run_dir),
        "plugin_guid": plugin_guid,
        "source_path": str(source_path),
        "dll_path": str(dll_path),
        "compile": compile_result,
        "build_log": str(build_log_path),
        "attempts": [],
    }

    if not compile_result.get("ok"):
        result["error"] = compile_result.get("error") or "plugin build failed"
        store.write_json(run_dir / "result.json", result)
        try:
            log_event("run_ui_plugin_probe", {"ok": False, "stage": result["stage"], "run_dir": result["run_dir"], "error": result.get("error")}, config=cfg)
        except Exception:
            pass
        return result

    if compile_only:
        result["ok"] = True
        result["stage"] = "compile"
        store.write_json(run_dir / "result.json", result)
        try:
            log_event("run_ui_plugin_probe", {"ok": True, "stage": result["stage"], "run_dir": result["run_dir"], "compile_only": True}, config=cfg)
        except Exception:
            pass
        return result

    attempts: list[dict[str, Any]] = []
    ini_candidates = _ini_candidates(cfg)
    for ini_path in ini_candidates:
        backend_id = f"ini:{ini_path}"
        attempts.append(
            _attempt_ini_backend(
                backend_id=backend_id,
                ini_path=ini_path,
                dll_path=dll_path,
                plugin_guid=plugin_guid,
                run_dir=run_dir,
                startup_wait_sec=startup_wait_sec,
                config=cfg,
            )
        )
        if attempts[-1].get("ok"):
            break

    if not any(item.get("ok") for item in attempts):
        for reg_path in _registry_candidates():
            backend_id = f"reg:{reg_path}"
            attempts.append(
                _attempt_registry_backend(
                    backend_id=backend_id,
                    registry_path=reg_path,
                    dll_path=dll_path,
                    plugin_guid=plugin_guid,
                    run_dir=run_dir,
                    startup_wait_sec=startup_wait_sec,
                    config=cfg,
                )
            )
            if attempts[-1].get("ok"):
                break

    result["attempts"] = attempts
    success = next((attempt for attempt in attempts if attempt.get("ok")), None)
    if success is not None:
        result["ok"] = True
        result["stage"] = "run"
        result["loaded_backend"] = success.get("backend")
        result["loaded_evidence_path"] = success.get("launch", {}).get("evidence_path")
    else:
        result["ok"] = False
        result["stage"] = "run"
        result["error"] = "UI plugin probe did not load in any attempted backend"
        blockers: list[str] = []
        for attempt in attempts:
            if attempt.get("error"):
                blockers.append(f"{attempt.get('backend')}: {attempt['error']}")
        if not blockers:
            blockers.append("No backend produced probe evidence (OnInitialize/OnCreateTools).")
        result["blockers"] = blockers

    store.write_json(run_dir / "result.json", result)
    try:
        log_event(
            "run_ui_plugin_probe",
            {
                "ok": result.get("ok"),
                "stage": result.get("stage"),
                "run_dir": result.get("run_dir"),
                "attempt_count": len(attempts),
                "loaded_backend": result.get("loaded_backend"),
                "error": result.get("error"),
            },
            config=cfg,
        )
    except Exception:
        pass
    return result
