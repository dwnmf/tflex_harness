import tomllib
from pathlib import Path


def test_pyproject_exposes_cli_and_mcp_entrypoints():
    pyproject = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))
    scripts = pyproject["project"]["scripts"]

    assert scripts["tflex-harness"] == "tflex_harness.cli:main"
    assert scripts["tflex-harness-mcp"] == "tflex_harness.mcp_server:main"
