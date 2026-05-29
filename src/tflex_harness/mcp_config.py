from __future__ import annotations

from typing import Any, Literal

from .config import HarnessConfig, load_config

MCP_CLIENTS = ("codex", "claude")


def generate_mcp_config(client: Literal["codex", "claude"] = "codex", config: HarnessConfig | None = None) -> dict[str, Any]:
    cfg = config or load_config()
    server = {
        "command": "tflex-harness-mcp",
        "env": {
            "TFLEX_HARNESS_REPO_DIR": str(cfg.repo_dir),
            "TFLEX_API_DOCS_DIR": str(cfg.docs_dir),
            "TFLEX_INSTALL_DIR": str(cfg.tflex_install_dir),
        },
    }
    return {
        "client": client,
        "mcpServers": {
            "tflex-harness": server,
        },
        "next": [
            "copy this JSON into your MCP config",
            "restart the MCP client",
            "call: get_tflex_environment",
        ],
    }


def _toml_string(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def generate_mcp_config_toml(config: HarnessConfig | None = None) -> str:
    cfg = config or load_config()
    env = {
        "TFLEX_HARNESS_REPO_DIR": str(cfg.repo_dir),
        "TFLEX_API_DOCS_DIR": str(cfg.docs_dir),
        "TFLEX_INSTALL_DIR": str(cfg.tflex_install_dir),
    }
    lines = [
        '[mcp_servers."tflex-harness"]',
        'command = "tflex-harness-mcp"',
        "",
        '[mcp_servers."tflex-harness".env]',
    ]
    lines.extend(f"{key} = {_toml_string(value)}" for key, value in env.items())
    return "\n".join(lines) + "\n"
