import json
import os
import subprocess
from pathlib import Path

from tflex_harness.config import load_config


def test_csharp_runner_skeleton_builds_and_reports_env():
    cfg = load_config()
    script = cfg.runner_dir / "build.ps1"
    proc = subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(script)], text=True, capture_output=True, timeout=60)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    exe = Path(proc.stdout.strip().splitlines()[-1])
    assert exe.exists()
    env = os.environ.copy()
    env["PATH"] = str(cfg.tflex_program_dir) + os.pathsep + env.get("PATH", "")
    run = subprocess.run([str(exe), "env"], text=True, capture_output=True, timeout=30, env=env)
    assert run.returncode == 0, run.stdout + run.stderr
    data = json.loads(run.stdout)
    assert data["ok"] is True
    assert data["is64BitProcess"] is True
    assert any(a["name"] == "TFlexAPI" for a in data["assemblies"])
