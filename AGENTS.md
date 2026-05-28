# T-FLEX Harness Agent Notes

This file records the current harness architecture from the live code under
`src/tflex_harness` as of 2026-05-28. Do not reconstruct architecture from old
or deleted notes when the code disagrees.

## Core Architecture

`tflex_harness` is a Python control plane around real T-FLEX CAD 17 execution.
Python owns CLI/MCP transport, config, docs search, diagnostics, artifacts,
recipe dispatch, prototype scanning, batch matrices, and logging. CAD API work
crosses the boundary as visible C# source compiled against local T-FLEX DLLs.

Keep this boundary:

- Python orchestrates.
- C# snippets and checked-in C# recipes execute T-FLEX API calls.
- Generated evidence lives in `artifacts/`.
- Candidate source lives in `agent_workspace/`.
- Reusable C# helper sources live in `src/tflex_harness/csharp_helpers/`.

Do not turn the harness into a broad Python CAD wrapper SDK unless the user asks
for that architectural change explicitly.

## Entry Points

- Package: `src/tflex_harness`.
- CLI script: `tflex-harness` -> `tflex_harness.cli:main`.
- MCP script: `tflex-harness-mcp` -> `tflex_harness.mcp_server:main`.
- Optional extras:
  - `.[mcp]` installs the MCP dependency.
  - `.[test]` installs pytest.

The MCP server is a thin adapter in `mcp_server.py`. It exposes:

- `search_tflex_docs`
- `get_tflex_environment`
- `run_csharp_tflex`
- `list_tflex_recipes`
- `run_tflex_recipe`
- `create_tflex_document`
- `run_tflex_document_factory_batch`
- `capture_tflex_state`
- `save_tflex_snippet_candidate`

The CLI exposes the same core loop plus bootstrap, prototype, factory, GRB
reverse, state, and UI-plugin probe commands.

## Configuration

`config.py` builds `HarnessConfig` from environment variables and defaults.
Important roots:

- `TFLEX_HARNESS_REPO_DIR` -> repo root override.
- `TFLEX_API_DOCS_DIR` -> local `tflex_api` docs checkout.
- `TFLEX_INSTALL_DIR` / `TFLEX_PROGRAM_DIR` -> T-FLEX CAD install/program dirs.
- `TFLEX_RUNNER_DIR` / `TFLEX_RUNNER_PROJECT` -> runner project dir.
- `TFLEX_ARTIFACTS_DIR` -> artifact root, default `artifacts`.
- `TFLEX_LOGS_DIR` -> logs root, default `logs`.
- `TFLEX_PROTOTYPES_DIR` -> prototype corpus override.

The code currently uses presence of `AGENTS.md`, `.agents`, and `install.md`
when trying to auto-detect the repo root. If repo-root detection changes, update
tests and this file together.

## Evidence And Artifacts

`ArtifactStore` in `artifacts.py` owns timestamped artifact directories:

- `artifacts/runs/<timestamp>_<slug>/`
- `artifacts/tflex_docs/<timestamp>_<slug>/`

Snippet and recipe runs persist observable evidence:

- `request.json`
- `snippet.cs`
- copied `helpers/*.cs` when helper sets are used
- `build.log`
- `stdout.txt`
- `stderr.txt`
- `run.log`
- `result.json`
- generated files under the run `artifacts/` directory

`logging_utils.py` appends JSONL events under `logs/`.

## Docs Search

`docs_search.py` is local-file search over the `tflex_api/llm` export:

- `symbols.jsonl`
- `types/*.md`
- `chm_pages.jsonl`
- `manifest.json`

`DocsIndex` owns freshness-aware loading and small in-memory caches.
`DocsSearch` owns scoring, scopes, assembly filters, and unified result shape.
Supported scopes are `symbols`, `types`, `chm`, and `all`.

Prefer exact local docs evidence before changing T-FLEX API code.

## C# Runner

`runner.py` owns C# snippet execution.

Current seams:

- `RunStore` creates run dirs and persists request/result evidence.
- `CompileCache` hashes C# code, selected T-FLEX references, compiler path, and
  helper source contents.
- `SnippetRunner` is the public orchestration class.
- `run_csharp_snippet(...)` is the function used by CLI, MCP, recipes, state
  probes, factory-generated C#, and tests.

Supported modes:

- `compile_only`
- `run`

Default references are local T-FLEX DLLs:

- `TFlexAPI.dll`
- `TFlexAPI3D.dll`
- `TFlexAPIData.dll`
- `TFlexCommandAPI.dll`

At run time the harness sets:

- `TFLEX_HARNESS_RUN_DIR`
- `TFLEX_HARNESS_ARTIFACTS_DIR`

Runner results must keep structured stages: `input`, `environment`, `compile`,
`run`, and `timeout`.

## C# Helper Sets

Reusable C# helper files are plain source files in
`src/tflex_harness/csharp_helpers/`. They are copied into each run and compiled
together with the visible snippet or recipe source. They are not hidden wrapper
DLLs.

Current helper-set names are defined in `runner.py`:

- `easy_core`
- `easy_session`
- `easy_3d`
- `easy_gears`
- `easy_export`
- `easy_prototype`
- `easy_variables`
- `easy_text`
- `easy_specification`
- `easy_document_properties`
- `easy_assembly_validation`
- `easy_modeling`
- `easy_part_features`
- `easy_reopen`
- `easy_assembly_build`
- `easy_mate_inspection`
- `easy_native_mates`
- `easy_all_live`
- `all`

When editing helper sets, update runner tests and recipe freshness expectations.

## Recipes

`recipes.py` owns verified recipe discovery and execution.

Recipe source and metadata live in `agent_workspace/recipes/`:

- `<name>.cs`
- `<name>.md`
- `<name>.recipe.json`

`RecipeRegistry` discovers metadata files, applies source/markdown SHA256
freshness checks, and marks stale recipes unverified. Markdown evidence must
contain the required live-verification phrases enforced by `recipes.py`.

`run_recipe(...)` resolves recipe args into environment variables and executes
the recipe source through `run_csharp_snippet(...)`.

Important invariant: explicit `output_file` for baseline document recipes must
stay under `artifacts/tflex_docs/`.

## Document Factory

`document_factory.py` maps JSON payloads into recipe plans or generated visible
C#.

Main flow:

1. Read payload JSON.
2. Write `input_payload.json` and `factory_plan.json` to a factory run dir.
3. Build a plan with `plan_document_creation(...)`.
4. Dispatch to:
   - a checked-in recipe,
   - `__factory_multi_step`, or
   - `__factory_fragment_lcs_assembly`.
5. Materialize requested outputs: GRB plus supported exports such as STEP, PDF,
   DXF, and DWG where implemented.
6. Write `factory_result.json`.

Generated factory C# must remain visible and evidence-backed.

`document_factory_batch.py` runs folders of payload JSON, reruns failed rows from
a matrix, supports open-only audit, and writes JSON/CSV/failure-report matrices.

## Prototypes

`prototypes.py` scans installed T-FLEX prototype files. It preserves Cyrillic
paths and indexes supported file types:

- `.grb`
- `.xml`
- `.txt`
- `.ico`

Prototype selectors can match id, relative path, absolute path, or name.

`prototype_validation.py` runs live/dry batch workflows for prototype open/save,
title/document property mutation, table cells, visible text, electrical labels,
and specification BOM fields.

`prototype_metadata.py` captures live metadata from copied `.grb` prototypes and
writes JSON/CSV indexes.

## State, Diagnostics, Bootstrap, UI Probe

- `diagnostics.py` checks T-FLEX install paths, DLLs, docs, Python, dotnet,
  `csc.exe`, MSBuild, runner skeleton, and live T-FLEX processes.
- `state.py` runs a read-only C# probe and parses live session/document state.
- `bootstrap.py` can clone/update docs, persist env vars, and register the Codex
  skill.
- `ui_plugin.py` compiles and probes a minimal T-FLEX UI plugin through INI or
  registry backends.
- `workspace.py` saves C# snippet candidates under `agent_workspace/snippets/`.
- `grb_reverse.py` turns GRB contour evidence JSON into semantic JSON and
  candidate parametric C#.

## Tests

Test roots:

- `tests/unit`
- `tests/smoke`
- `tests/integration`

Pytest markers:

- `integration` requires live T-FLEX CAD.
- `smoke` covers local tooling.

Validation ladder:

1. For pure Python changes, run targeted unit tests first.
2. For CLI/MCP contract changes, run targeted smoke tests.
3. For T-FLEX API shape, run `run-csharp --mode compile_only` first.
4. For live behavior claims, run a live recipe/probe and cite the run dir.

Do not claim live T-FLEX behavior works without live evidence for that exact
path.

## Agent Work Rules

- Run `git status --short` before tracked edits.
- Do not touch unrelated untracked files or generated artifacts.
- Do not commit `artifacts/`, `logs/`, caches, or run outputs unless explicitly
  asked.
- Use exact search first: `rg`, `fff`, local docs grep.
- For T-FLEX API behavior, verify local docs and, when needed, DeepWiki
  `dwnmf/tflex_api`.
- Keep MCP tools thin. Prefer improving internal seams over adding broad public
  CAD-specific tools.
- Keep snippets, recipes, generated factory C#, and helper sources visible.
- Preserve structured JSON result contracts unless tests and user request justify
  a breaking change.
