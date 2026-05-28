from pathlib import Path

from tflex_harness.config import HarnessConfig
from tflex_harness.mcp_config import generate_mcp_config


def test_generate_mcp_config_contains_required_env():
    cfg = HarnessConfig(
        repo_dir=Path("C:/tflex_harness"),
        docs_dir=Path("C:/tflex_api"),
        tflex_install_dir=Path("C:/Program Files/T-FLEX CAD 17"),
        tflex_program_dir=Path("C:/Program Files/T-FLEX CAD 17/Program"),
        runner_dir=Path("C:/tflex_harness/runner/TFlexRunner"),
        artifacts_dir=Path("C:/tflex_harness/artifacts"),
        logs_dir=Path("C:/tflex_harness/logs"),
    )

    config = generate_mcp_config("codex", cfg)
    server = config["mcpServers"]["tflex-harness"]

    assert config["client"] == "codex"
    assert server["command"] == "tflex-harness-mcp"
    assert server["env"]["TFLEX_HARNESS_REPO_DIR"] == "C:\\tflex_harness"
    assert server["env"]["TFLEX_API_DOCS_DIR"] == "C:\\tflex_api"
    assert server["env"]["TFLEX_INSTALL_DIR"] == "C:\\Program Files\\T-FLEX CAD 17"
    assert "call: get_tflex_environment" in config["next"]
