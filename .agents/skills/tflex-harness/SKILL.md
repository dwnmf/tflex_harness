---
name: tflex-harness
description: "Work on the local <repo> repository: T-FLEX CAD 17 harness/MCP code, C# snippet runner, recipes, live CAD validation, artifacts, diagnostics, and project documentation. Use this when editing, testing, debugging, or operating tflex-harness itself. Communicate in a concise caveman style while preserving exact commands, paths, and evidence."
---

# T-FLEX Harness

Use this skill for work inside `<repo>`: harness code, MCP server, C# snippet runner, recipes, live T-FLEX CAD checks, generated artifacts, diagnostics, and local project docs.

Keep this file lean. Detailed facts moved to `references/`; load only the file needed for the task.

## Voice

User-facing style:

- Caveman concise. Short sentences. No fluff.
- Keep exact technical names: paths, commands, APIs, run dirs, errors.
- Do not hide uncertainty. Say “Not verified”, “Need live T-FLEX”, or “Not know yet”.
- Report evidence, not vibes.

## Repo Map

- Repo root: `<repo>`
- Package: `src/tflex_harness`
- Tests: `tests/unit`, `tests/smoke`, `tests/integration`
- Local skills: `.agents/skills`
- Generated run dirs: `artifacts/runs`
- Generated T-FLEX files: `artifacts/tflex_docs`
- Snippet candidates: `agent_workspace/snippets`
- C# helper sources: `src/tflex_harness/csharp_helpers`
- Event log: `logs/events.jsonl`
- Architecture/status: `goal.md`
- Public install guide: `install.md`
- Public agent skill: `SKILL.md`
- T-FLEX API docs source: `https://github.com/dwnmf/tflex_api`
- Local T-FLEX API docs: `<tflex-api-docs>\llm`

## Reference Map

Read these only when task needs them:

- `references/current-focus-assembly-validation.md` — historical assembly-validation MVP state, live evidence, and do-not-rerun rule.
- `references/install-release.md` — public install, API docs install, MCP entrypoint, release asset rule.
- `references/commands-and-runner.md` — common commands, direct C# runner, live session setup.
- `references/csharp-helpers-and-gears.md` — helper sets and gear-specific modeling rules.
- `references/verified-api-facts.md` — verified export, variables, primitive solids, transformations.
- `references/fragments-mates-selection.md` — Fragment3D LCS path, native mate failures/status, freedom, selection, forum context, hypotheses.

## Current Focus Short

Current active work comes from `goal.md`. As of 2026-05-27, that file tracks helper backlog implementation.

Before assembly-validation work, read `references/current-focus-assembly-validation.md` too.

Do not rerun broad prototype/document batches for this goal. Use only targeted live recipe/probes.

## Hard Rules

1. Run `git status --short` before tracked edits.
2. Do not commit generated artifacts unless user explicitly asks.
3. Do not touch unrelated untracked files. Known old untracked path may exist: `agent_workspace/snippets/crank_yoke_assembly/`.
4. Use exact search first: `rg`, `fff`, local docs grep.
5. For T-FLEX API behavior, also use `deepwiki-tflex-api`.
6. Prefer smallest validation:
   - Harness code: targeted unit/smoke test.
   - T-FLEX API shape: `compile_only` first.
   - T-FLEX behavior: live run only when needed.
7. For live snippets, capture run dir and stdout evidence.
8. If a live snippet prints success but times out, inspect `result.json`, `stdout.txt`, saved `.grb`, and stale `Snippet` process before judging failure.
9. Do not claim native T-FLEX behavior works without a live run proving the exact path.

## Workflows

### Install/release

Read `references/install-release.md`.

### C# snippets and T-FLEX API

1. Use explicit references:
   - `TFlexAPI` for application/session/document/2D API.
   - `TFlexAPI3D` for 3D operations, geometry, fragments, mates.
   - `TFlexCommandAPI` for command/UI API only.
   - `TFlexAPIData` for data API only.
2. For snippet-generated outputs, write under `TFLEX_HARNESS_ARTIFACTS_DIR` / `EasySession.ArtifactPath(...)`. Do not write `.grb`/STEP files into random repo or user folders.
3. For exact runner commands and live session setup, read `references/commands-and-runner.md`.
4. Use helper `.cs` files when they prevent repeated T-FLEX API mistakes. Helper sources compile with the visible snippet, not as hidden wrapper DLLs. For helper sets, read `references/csharp-helpers-and-gears.md`.

### Validation Ladder

Harness code:

1. Run the narrowest relevant unit test.
2. Run related smoke test.
3. Run integration only if live T-FLEX is required and scope allows.

T-FLEX API snippets:

1. Search `<tflex-api-docs>\llm\symbols.jsonl`.
2. Open matching `<tflex-api-docs>\llm\types\*.md`.
3. Ask DeepWiki repo `dwnmf/tflex_api` for exact class/member behavior.
4. Compile with `mode='compile_only'`.
5. Run live if compile passes and behavior matters.
6. Save evidence under `artifacts/runs/...` and `.grb` outputs under `artifacts/tflex_docs/...`.

### Fragile verified facts

- For export/variables/primitives/transforms, read `references/verified-api-facts.md` before changing behavior.
- For fragments, LCS, mates, freedom, selection, and native mate hypotheses, read `references/fragments-mates-selection.md` before changing behavior.

## Reporting Template

Use this shape:

```text
Done. Me checked.

Changed:
- `path`

Verified:
- `command or run dir`

Not verified:
- Exact gap.
```

Rules:

- Separate `Changed`, `Verified`, and `Not verified` when edits or partial validation exist.
- Include run dirs for live T-FLEX evidence.
- Mention if generated artifacts were intentionally not committed.
- Mention if commit/push happened and include commit hash.
