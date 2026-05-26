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
- T-FLEX API docs at `<tflex-api-docs>` or set `TFLEX_API_DOCS_DIR`.
- Default T-FLEX install: `<tflex-install>`; override with `TFLEX_INSTALL_DIR` or `TFLEX_PROGRAM_DIR`.

## Human install

Clone once into a stable path and install editable so CLI/MCP always sees the repo recipes and helper sources:

```powershell
git clone https://github.com/dwnmf/tflex_harness <repo>
cd <repo>
uv tool install -e ".[mcp]"
tflex-harness env
tflex-harness recipes
```

If you install from a GitHub release wheel instead of editable source, set the repo path when you want checked-in recipes:

```powershell
$env:TFLEX_HARNESS_REPO_DIR = "<repo>"
```

For persistent Windows user env:

```powershell
setx TFLEX_HARNESS_REPO_DIR "<repo>"
```

## MCP server

CLI entrypoint:

```powershell
tflex-harness-mcp
```

Codex/Claude-style MCP config example:

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

Read `install.md` first. Install the repo into a durable local path, preferably <repo> on Windows. Install it editable with MCP extras (`uv tool install -e ".[mcp]"`). Verify `tflex-harness env`, `tflex-harness recipes`, and one compile-only C# snippet. Then register this repo's `SKILL.md` as a global agent skill so future sessions know how to use the harness. Do not run broad live prototype batches during setup; use only small verification commands unless I ask for more.
```

Register skill for Codex on Windows:

```powershell
$skillRoot = Join-Path ($env:CODEX_HOME ?? "$env:USERPROFILE\.codex") "skills\tflex-harness"
New-Item -ItemType Directory -Force -Path $skillRoot | Out-Null
Copy-Item -Force .\SKILL.md (Join-Path $skillRoot "SKILL.md")
```

If symlinks are available and you want the skill to update with the repo:

```powershell
$skillRoot = Join-Path ($env:CODEX_HOME ?? "$env:USERPROFILE\.codex") "skills\tflex-harness"
New-Item -ItemType Directory -Force -Path $skillRoot | Out-Null
New-Item -ItemType SymbolicLink -Force -Path (Join-Path $skillRoot "SKILL.md") -Target (Resolve-Path .\SKILL.md)
```

Claude Code can import this file from its global memory, for example:

```text
@<repo>\SKILL.md
```

## Verification ladder

Fast install checks:

```powershell
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

## Release install

Download the latest GitHub release assets:

- `tflex_harness-<version>-py3-none-any.whl`
- `tflex_harness-<version>.tar.gz`

Install wheel as a tool:

```powershell
uv tool install .\tflex_harness-0.2.0-py3-none-any.whl --with mcp
```

For full recipe/helper workspace behavior, still keep a repo checkout and set `TFLEX_HARNESS_REPO_DIR`.

## Maintenance

Update editable install:

```powershell
cd <repo>
git pull --ff-only
uv tool install -e ".[mcp]" --force
tflex-harness env
```

Important paths:

- Repo: `<repo>`
- T-FLEX docs: `<tflex-api-docs>`
- Artifacts: `artifacts/runs`, `artifacts/tflex_docs`
- Helper sources: `src/tflex_harness/csharp_helpers`
- Recipes: `agent_workspace/recipes`
