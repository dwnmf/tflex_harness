from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class HarnessConfig:
    repo_dir: Path
    docs_dir: Path
    tflex_install_dir: Path
    tflex_program_dir: Path
    runner_dir: Path
    artifacts_dir: Path
    logs_dir: Path

    @property
    def docs_llm_dir(self) -> Path:
        return self.docs_dir / "llm"

    @property
    def symbols_jsonl(self) -> Path:
        return self.docs_llm_dir / "symbols.jsonl"

    @property
    def chm_pages_jsonl(self) -> Path:
        return self.docs_llm_dir / "chm_pages.jsonl"

    @property
    def types_dir(self) -> Path:
        return self.docs_llm_dir / "types"

    @property
    def manifest_json(self) -> Path:
        return self.docs_llm_dir / "manifest.json"

    def tflex_dll(self, name: str) -> Path:
        return self.tflex_program_dir / name


def find_repo_dir(start: Path | None = None) -> Path:
    current = (start or Path(__file__).resolve()).resolve()
    if current.is_file():
        current = current.parent
    for parent in [current, *current.parents]:
        if (parent / "goal.md").exists() and (parent / ".agents").exists():
            return parent
    return Path.cwd().resolve()


def load_config(repo_dir: Path | None = None) -> HarnessConfig:
    repo = (repo_dir or find_repo_dir()).resolve()
    install = Path(os.environ.get("TFLEX_INSTALL_DIR", r"C:\Program Files\T-FLEX CAD 17"))
    program = Path(os.environ.get("TFLEX_PROGRAM_DIR", str(install / "Program")))
    docs = Path(os.environ.get("TFLEX_API_DOCS_DIR", r"D:\REALPROJECTS\tflex_api"))
    return HarnessConfig(
        repo_dir=repo,
        docs_dir=docs,
        tflex_install_dir=install,
        tflex_program_dir=program,
        runner_dir=Path(os.environ.get("TFLEX_RUNNER_DIR", str(repo / "runner" / "TFlexRunner"))),
        artifacts_dir=Path(os.environ.get("TFLEX_ARTIFACTS_DIR", str(repo / "artifacts"))),
        logs_dir=Path(os.environ.get("TFLEX_LOGS_DIR", str(repo / "logs"))),
    )
