import json
import os
import subprocess
from pathlib import Path

from tflex_harness.config import load_config
from tflex_harness.runner import build_runner


def test_csharp_runner_skeleton_builds_and_reports_env():
    cfg = load_config()
    for name in ["Program.cs", "SnippetHost.cs", "TFlexSession.cs", "ResultWriter.cs", "References.props", "TFlexRunner.csproj"]:
        assert (cfg.runner_dir / name).exists()
    result = build_runner(timeout_sec=60, config=cfg)
    assert result["ok"] is True, result
    assert result["stage"] == "build"
    exe = Path(result["executable"])
    assert exe.exists()
    env = os.environ.copy()
    env["PATH"] = str(cfg.tflex_program_dir) + os.pathsep + env.get("PATH", "")
    run = subprocess.run([str(exe), "env"], text=True, capture_output=True, timeout=30, env=env)
    assert run.returncode == 0, run.stdout + run.stderr
    data = json.loads(run.stdout)
    assert data["ok"] is True
    assert data["is64BitProcess"] is True
    assert any(a["name"] == "TFlexAPI" for a in data["assemblies"])
