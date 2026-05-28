---
name: tflex-install
description: Install and bootstrap tflex-harness as a CLI/MCP server for T-FLEX CAD 17, then register the agent skill.
---

# tflex-harness install

Use this file only for first-time install, reconnect, release install, or cold-start bootstrap. For normal agent usage, read `SKILL.md`.

`tflex-harness` is intentionally thin:

- Python = CLI/MCP control plane, docs search, artifacts, process execution.
- C# snippets = visible T-FLEX CAD 17 API work.
- Helpers = checked-in `.cs` source compiled with snippets, not hidden DLL wrappers.

## Requirements

- Windows with T-FLEX CAD 17 installed.
- Python 3.11+.
- `uv` recommended.
- `git` for automatic docs clone.
- Default T-FLEX install: `<tflex-install>`; override with `TFLEX_INSTALL_DIR` or `TFLEX_PROGRAM_DIR`.

## Simple install

Recommended path: clone once, install editable, let `bootstrap` do the rest.

```powershell
git clone https://github.com/dwnmf/tflex_harness <repo>
cd <repo>
uv tool install -e ".[mcp]"
tflex-harness bootstrap --full
```

What `bootstrap --full` does:

- clones T-FLEX API docs from `https://github.com/dwnmf/tflex_api` into sibling `<repo>\..\tflex_api` when missing;
- sets `TFLEX_HARNESS_REPO_DIR` and `TFLEX_API_DOCS_DIR` for future terminals;
- copies root `SKILL.md` into Codex global skills;
- checks docs completeness;
- runs install readiness checks for T-FLEX paths, docs, Python, git, uv, dotnet, csc, and runner setup.

Restart the terminal after `--full`.

Use `tflex-harness doctor` when setup fails. It reports install checks and fix commands for missing T-FLEX paths, docs, repo checkout, compilers, and runner setup.

Optional follow-up checks:

```powershell
tflex-harness recipes
tflex-harness run-csharp --mode compile_only --code "public class Program { public static int Main(){ return 0; } }"
```

If you do not have `uv`:

```powershell
py -m pip install -e ".[mcp]"
python -m tflex_harness.cli bootstrap --full
```

## Custom docs path

Use this only when docs must live outside the default sibling path:

```powershell
git clone https://github.com/dwnmf/tflex_api <tflex-api-docs>
cd <repo>
uv tool install -e ".[mcp]"
tflex-harness bootstrap --docs-dir "<tflex-api-docs>" --full
```

If you install from a GitHub release wheel instead of editable source, keep a repo checkout and persist the repo path:

```powershell
tflex-harness bootstrap --docs-dir "<tflex-api-docs>" --full
```

## Bootstrap options

```powershell
tflex-harness bootstrap --help
```

Useful flags:

- `--docs-dir <path>` — use a custom T-FLEX API docs checkout.
- `--full` — recommended first install: docs clone when missing, persisted env, Codex skill registration, and checks.
- `--update-docs` — run `git pull --ff-only` in an existing docs checkout.
- `--no-docs` — skip docs clone/update.
- `--persist-env` — persist `TFLEX_HARNESS_REPO_DIR` and `TFLEX_API_DOCS_DIR`.
- `--register-codex-skill` — copy root `SKILL.md` into Codex global skills.
- `--symlink-skill` — prefer a symlink instead of copying `SKILL.md`.
- `--no-checks` — skip docs completeness checks.

## MCP server

CLI entrypoint:

```powershell
tflex-harness-mcp
```

Generate ready-to-copy config:

```powershell
tflex-harness mcp-config --for codex
tflex-harness mcp-config --for claude
```

Codex/Claude-style MCP config shape:

```json
{
  "mcpServers": {
    "tflex-harness": {
      "command": "tflex-harness-mcp",
      "env": {
        "TFLEX_HARNESS_REPO_DIR": "<repo>",
        "TFLEX_API_DOCS_DIR": "<tflex-api-docs>",
        "TFLEX_INSTALL_DIR": "<tflex-install>"
      }
    }
  }
}
```

## AI agent install

Paste this into Codex or Claude Code:

```text
Set up https://github.com/dwnmf/tflex_harness for me.

Read `install.md` first. Install the repo into a durable local path, preferably <repo> on Windows. Install editable with MCP extras (`uv tool install -e ".[mcp]"`). Then run `tflex-harness bootstrap --full`; it performs install readiness checks. Optional follow-up checks are `tflex-harness recipes` and one compile-only C# snippet. Do not run broad live prototype batches during setup; use only small verification commands unless I ask for more.
```

Claude Code can import this file from its global memory, for example:

```text
@<repo>\SKILL.md
```

## Verification ladder

Fast install checks:

```powershell
tflex-harness doctor
tflex-harness env
tflex-harness recipes
```

Compile-only C# check:

```powershell
tflex-harness run-csharp --mode compile_only --code "public class Program { public static int Main(){ return 0; } }"
```

Small live T-FLEX check only when CAD is available:

```powershell
tflex-harness run-recipe helper_assembly_validation --timeout-sec 120
```

## Wheel install status

Editable clone is the recommended public install today. Wheel installs are secondary because full recipe/helper workspace behavior still needs a repo checkout and `TFLEX_HARNESS_REPO_DIR`.

Release assets are built by `.github/workflows/release-build.yml` on `v*` tags. If the tag release already exists, the workflow uploads assets with `--clobber` and updates release title/notes. For manual release updates, run the workflow with `publish_release=true` and `tag=v<version>`.

- `tflex_harness-<version>-py3-none-any.whl`
- `tflex_harness-<version>.tar.gz`

Download the release assets:

- `tflex_harness-<version>-py3-none-any.whl`
- `tflex_harness-<version>.tar.gz`

Install wheel as a tool:

```powershell
uv tool install .\tflex_harness-0.2.1-py3-none-any.whl --with mcp
```

For full recipe/helper workspace behavior, still keep a repo checkout and set `TFLEX_HARNESS_REPO_DIR`.

## Maintenance

Update editable install:

```powershell
cd <repo>
git pull --ff-only
uv tool install -e ".[mcp]" --force
tflex-harness bootstrap --update-docs --full
tflex-harness env
```

Important paths:

- Repo: `<repo>`
- T-FLEX docs: `<tflex-api-docs>`
- Artifacts: `artifacts/runs`, `artifacts/tflex_docs`
- Helper sources: `src/tflex_harness/csharp_helpers`
- Recipes: `agent_workspace/recipes`

## Install CI contract

`.github/workflows/install-smoke.yml` runs on `windows-latest` without live T-FLEX CAD. It checks editable install, command discovery, `bootstrap --no-docs --no-checks`, recipe listing, MCP config generation, doctor output, and safe install smoke tests.

`.github/workflows/release-build.yml` builds wheel + sdist, smoke-installs the wheel, uploads package artifacts, and creates or updates release assets when a `v*` tag is pushed or when manually run with `publish_release=true` and `tag=v<version>`.
