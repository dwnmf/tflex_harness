from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path
from typing import Any

from .config import load_config
from .diagnostics import check_docs_repo

DEFAULT_DOCS_URL = "https://github.com/dwnmf/tflex_api"


def _run(command: list[str], *, cwd: Path | None = None, timeout: int = 120) -> dict[str, Any]:
    try:
        proc = subprocess.run(command, cwd=cwd, text=True, capture_output=True, timeout=timeout)
        return {
            "ok": proc.returncode == 0,
            "returncode": proc.returncode,
            "command": command,
            "stdout": proc.stdout.strip(),
            "stderr": proc.stderr.strip(),
        }
    except Exception as exc:
        return {"ok": False, "command": command, "error": str(exc)}


def _set_user_env(name: str, value: Path | str) -> dict[str, Any]:
    text = str(value)
    os.environ[name] = text
    if os.name != "nt":
        return {"ok": False, "name": name, "value": text, "skipped": "setx is Windows-only"}
    if not shutil.which("setx"):
        return {"ok": False, "name": name, "value": text, "error": "setx not found"}
    result = _run(["setx", name, text], timeout=30)
    result.update({"name": name, "value": text})
    return result


def _codex_skills_dir() -> Path:
    codex_home = os.environ.get("CODEX_HOME")
    if codex_home:
        return Path(codex_home).expanduser() / "skills"
    return Path.home() / ".codex" / "skills"


def _register_codex_skill(repo_dir: Path, *, symlink: bool = False) -> dict[str, Any]:
    source = repo_dir / "SKILL.md"
    target_dir = _codex_skills_dir() / "tflex-harness"
    target = target_dir / "SKILL.md"
    if not source.exists():
        return {"ok": False, "source": str(source), "target": str(target), "error": "source SKILL.md missing"}
    target_dir.mkdir(parents=True, exist_ok=True)
    if target.exists() or target.is_symlink():
        target.unlink()
    if symlink:
        try:
            target.symlink_to(source)
            return {"ok": True, "mode": "symlink", "source": str(source), "target": str(target)}
        except OSError as exc:
            copied = shutil.copy2(source, target)
            return {"ok": True, "mode": "copy", "source": str(source), "target": str(copied), "symlink_error": str(exc)}
    copied = shutil.copy2(source, target)
    return {"ok": True, "mode": "copy", "source": str(source), "target": str(copied)}


def bootstrap(
    *,
    docs_dir: str | None = None,
    docs_url: str = DEFAULT_DOCS_URL,
    no_docs: bool = False,
    update_docs: bool = False,
    persist_env: bool = False,
    register_codex_skill: bool = False,
    symlink_skill: bool = False,
    no_checks: bool = False,
) -> dict[str, Any]:
    cfg = load_config()
    repo_dir = cfg.repo_dir
    resolved_docs_dir = Path(docs_dir).expanduser().resolve() if docs_dir else cfg.docs_dir.resolve()

    actions: list[dict[str, Any]] = []
    blockers: list[str] = []

    if not no_docs:
        if resolved_docs_dir.exists():
            actions.append({"ok": True, "action": "docs_present", "path": str(resolved_docs_dir)})
            if update_docs and (resolved_docs_dir / ".git").exists():
                pull = _run(["git", "pull", "--ff-only"], cwd=resolved_docs_dir, timeout=120)
                pull["action"] = "docs_update"
                actions.append(pull)
                if not pull["ok"]:
                    blockers.append(f"docs update failed: {resolved_docs_dir}")
        else:
            if not shutil.which("git"):
                blockers.append("git not found; cannot clone T-FLEX API docs")
                actions.append({"ok": False, "action": "docs_clone", "path": str(resolved_docs_dir), "error": "git not found"})
            else:
                resolved_docs_dir.parent.mkdir(parents=True, exist_ok=True)
                clone = _run(["git", "clone", docs_url, str(resolved_docs_dir)], timeout=300)
                clone["action"] = "docs_clone"
                actions.append(clone)
                if not clone["ok"]:
                    blockers.append(f"docs clone failed: {resolved_docs_dir}")

    env: list[dict[str, Any]] = []
    if persist_env:
        env.append(_set_user_env("TFLEX_HARNESS_REPO_DIR", repo_dir))
        env.append(_set_user_env("TFLEX_API_DOCS_DIR", resolved_docs_dir))
        for item in env:
            if not item.get("ok"):
                blockers.append(f"persist env failed: {item.get('name')}")
    else:
        os.environ["TFLEX_HARNESS_REPO_DIR"] = str(repo_dir)
        os.environ["TFLEX_API_DOCS_DIR"] = str(resolved_docs_dir)

    skill = None
    if register_codex_skill:
        skill = _register_codex_skill(repo_dir, symlink=symlink_skill)
        if not skill.get("ok"):
            blockers.append("Codex skill registration failed")

    checks = None
    if not no_checks:
        checks = {"docs": check_docs_repo(load_config(repo_dir))}
        docs_ok = checks["docs"]["symbols_jsonl"] and checks["docs"]["chm_pages_jsonl"] and checks["docs"]["types_dir"]
        if not docs_ok:
            blockers.append(f"T-FLEX API docs incomplete: {resolved_docs_dir}")

    return {
        "ok": not blockers,
        "repo_dir": str(repo_dir),
        "docs_dir": str(resolved_docs_dir),
        "actions": actions,
        "persist_env": persist_env,
        "env": env,
        "skill": skill,
        "checks": checks,
        "blockers": blockers,
        "next": [
            "restart terminal after --persist-env",
            "run: tflex-harness env",
            "run: tflex-harness recipes",
        ],
    }
