# Install and Release Pattern

## Contents
- Public install pattern
- API docs install
- MCP entrypoint
- Release asset rule

## Install/Release Pattern

Public install is modeled after browser-harness:

- Human install: clone repo, `uv tool install -e ".[mcp]"`, verify `tflex-harness env` and `tflex-harness recipes`.
- API docs install: clone `https://github.com/dwnmf/tflex_api` to `<tflex-api-docs>` and set `TFLEX_API_DOCS_DIR`; fallback is sibling checkout named `tflex_api`.
- AI install: read root `install.md`, then register root `SKILL.md` as a global agent skill.
- MCP entrypoint: `tflex-harness-mcp`.
- If a non-editable wheel install cannot find recipes/helpers, set `TFLEX_HARNESS_REPO_DIR` to the repo checkout.
- Release assets should include wheel + sdist from `python -m build`; do not commit `dist/`.
