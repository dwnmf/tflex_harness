# T-FLEX Harness Architecture Decisions

Date: 2026-05-24. Scope: architecture note only; no code change.

## Moderator Summary

- **Round output:** Keep this as an architecture decision note, not an implementation plan.
- **Decision to carry forward:** Python stays the thin control plane; C# stays the only T-FLEX API execution boundary.
- **Allowed future seams:** Only `DocsIndex`, `RunStore/CompileCache/SnippetRunner`, and `RecipeRegistry`.
- **Next useful round:** Gather measurement evidence and contract snapshots before approving any refactor.

## Status

This project should stay a thin, evidence-driven harness around the real T-FLEX CAD 17 API. The architecture work below is not a request to add features now. It defines the boundaries to preserve and the evidence gates that must be met before refactoring.

## Decisions

1. **Python remains the control plane.** Python owns MCP/CLI transport, docs search, diagnostics, subprocess execution, artifacts, logs, and recipe registry glue.
2. **C# remains the only T-FLEX API execution boundary.** Visible C# snippets/recipes are the contract for real CAD API work.
3. **Keep exactly three internal seams for future simplification:** `DocsIndex`, `RunStore/CompileCache/SnippetRunner`, and `RecipeRegistry`.
4. **Do not grow the public MCP surface now.** Preserve the docs/run/observe loop unless measurements prove a new public tool is necessary.

## Evidence Baseline

- `README.md:5` states the current split: Python is the thin control plane; C# snippets execute against the real T-FLEX CAD 17 .NET API.
- `goal.md:5`, `goal.md:7`, and `goal.md:9`-`goal.md:11` define the product goal: a thin, verifiable harness, not a broad CAD framework.
- `goal.md:43`-`goal.md:48` explicitly rejects many prebuilt CAD wrapper tools and keeps the agent writing real C# against the API.
- `goal.md:63` says the harness must not become an alternative T-FLEX SDK.
- `goal.md:101`-`goal.md:102` records the intended split: Python for harness/MCP/control/docs/logs; C# for actual API execution/data plane.
- `README.md:23`-`README.md:31` lists the current public tools: docs search, environment, C# run, recipes, state capture, and snippet candidate save.
- `src/tflex_harness/mcp_server.py:24`, `src/tflex_harness/mcp_server.py:34`, `src/tflex_harness/mcp_server.py:39`, and `src/tflex_harness/mcp_server.py:44` show MCP functions forwarding to internal docs/runner/recipe boundaries.
- `src/tflex_harness/docs_search.py:44`, `src/tflex_harness/docs_search.py:90`, `src/tflex_harness/docs_search.py:96`, and `src/tflex_harness/docs_search.py:116` show docs search already has one module boundary, but only symbols are loaded through a cached helper while type pages and CHM search scan files directly.
- `src/tflex_harness/runner.py:88`, `src/tflex_harness/runner.py:105`, `src/tflex_harness/runner.py:219`, and `src/tflex_harness/runner.py:242` show compile-cache, run persistence, and runner orchestration are currently colocated.
- `src/tflex_harness/recipes.py:10`, `src/tflex_harness/recipes.py:75`, `src/tflex_harness/recipes.py:92`, and `src/tflex_harness/recipes.py:115`-`src/tflex_harness/recipes.py:144` show recipes use a manual Python registry plus per-recipe execution/output handling.
- Prior local command observations in the previous architecture note reported `env` and `recipes` output, but no durable run dir or captured stdout path was attached. Treat those observations as useful context, not as sufficient proof for implementation decisions.

## Invariants

- The user-facing loop is: search docs -> write visible C# -> compile/run -> observe diagnostics/artifacts -> refine -> promote verified recipe.
- Snippet and recipe source must remain visible and artifacted.
- Compile errors, runtime errors, T-FLEX exceptions, timeouts, stdout/stderr, and generated artifacts must stay observable.
- Internal refactors must preserve current MCP/CLI behavior unless a separate evidence-gated decision changes it.

## Non-Goals

- No broad CAD wrapper framework.
- No public `create_line`, `create_extrusion`, `make_drawing`, or similar CAD-specific MCP tool set.
- No long-lived T-FLEX session as the default execution mode.
- No hidden Python/COM automation path as the primary API execution route.
- No new public MCP contract until measurements show the current docs/run/observe loop is insufficient.

## Subsystem Map

| Area | Current files | Role | Architectural boundary |
|---|---|---|---|
| Transport adapters | `src/tflex_harness/cli.py`, `src/tflex_harness/mcp_server.py` | Convert CLI/MCP payloads to internal calls | Keep thin; no CAD semantics here |
| Documentation search | `src/tflex_harness/docs_search.py` | Search symbols, type pages, and CHM corpus | Candidate seam: `DocsIndex` |
| Execution and evidence | `src/tflex_harness/runner.py`, `src/tflex_harness/artifacts.py`, `src/tflex_harness/logging_utils.py` | Compile/run snippets, cache builds, persist requests/results/events/artifacts | Candidate seam: `RunStore/CompileCache/SnippetRunner` |
| Environment/state probes | `src/tflex_harness/diagnostics.py`, `src/tflex_harness/state.py` | Report install/docs/toolchain/process/live document state | Stay as observable probes; do not become CAD wrappers |
| Recipes | `src/tflex_harness/recipes.py`, `agent_workspace/recipes/*` | List and run verified C# recipes | Candidate seam: `RecipeRegistry` |
| Documentation of intent | `goal.md`, `README.md`, this file | Preserve boundaries, operator commands, and evidence rules | Must stay evidence-gated |

## Change Card 1: `DocsIndex`

**Decision:** Introduce `DocsIndex` only behind the existing `search_tflex_docs`/CLI search contract.

**Why this boundary:** Docs search already owns symbols/types/CHM lookup in one module. Evidence shows `search_types` walks `types_dir.glob("*.md")` and `search_chm` reads CHM JSONL during search, while only symbols go through cached loading.

**Evidence gate before implementation:**

- Measure cold and warm latency for `search --scope symbols`, `search --scope types`, `search --scope chm`, and `search --scope all`.
- Record output to a durable artifact or terminal log included in the follow-up note.
- Proceed only if repeated file scanning is a material delay in the agent loop or causes measurable churn.

**Not now:**

- Do not change the public query/result shape.
- Do not add a database service.
- Do not replace exact local docs evidence with semantic-only retrieval.

**Acceptance evidence if implemented later:**

- Existing docs search tests still pass.
- Measured warm search latency improves or stays stable.
- Index invalidation is tied to local docs manifest/file freshness.

## Change Card 2: `RunStore/CompileCache/SnippetRunner`

**Decision:** Split runner internals only along existing responsibilities: run persistence, compile cache, and snippet orchestration.

**Why this boundary:** `runner.py` currently owns cache key/dir, compile/run orchestration, artifact paths, result persistence, event logging, and runtime environment variables. Those are real responsibilities, but they are still one public use case: compile/run visible C#.

**Evidence gate before implementation:**

- Show concrete maintenance or behavior pressure: repeated bugs around artifact persistence, cache behavior, timeout reporting, or future execution modes.
- Measure cold and warm `run-csharp --mode compile_only` to separate compile cache value from orchestration overhead.
- Capture at least one current `run-csharp --mode run` contract snapshot, including result fields and run-dir files.
- Add or identify tests that cover the compile and run result contracts before moving code.

**Not now:**

- Do not add long-lived CAD sessions to the default path.
- Do not hide C# source behind opaque commands.
- Do not create a generic workflow framework.

**Acceptance evidence if implemented later:**

- `run_csharp_tflex` and CLI `run-csharp` return the same result fields as before.
- Run dirs still contain request/result/stdout/stderr/build/run logs and collected artifacts.
- Cache hit/miss behavior remains visible in results and logs.

## Change Card 3: `RecipeRegistry`

**Decision:** Move recipe truth toward co-located metadata only after freshness rules are explicit.

**Why this boundary:** Recipes are verified C# assets, but the current registry is a manual Python tuple while recipe source and Markdown evidence live in `agent_workspace/recipes`. Output-file policy also lives in Python control flow.

**Evidence gate before implementation:**

- Define the minimal metadata fields: `name`, `description`, `args`, `verified`, `last_verified`, `source`, `evidence`, and limitations.
- Define freshness rules: what makes `verified=true` stale when C# source, Markdown evidence, or live-run evidence changes.
- Include a source hash, evidence run id, or equivalent proof so recipe verification cannot survive unrelated edits silently.
- Keep current Python registry as compatibility fallback until tests prove metadata discovery.

**Not now:**

- Do not auto-promote snippets into verified recipes.
- Do not trust Markdown claims without source/evidence freshness checks.
- Do not widen recipe output paths beyond `artifacts/tflex_docs`.

**Acceptance evidence if implemented later:**

- `list_tflex_recipes` still reports existing recipes and source/Markdown existence.
- Unit/smoke tests prove stale or missing evidence cannot silently appear as verified.
- `run_tflex_recipe` still uses the same C# snippet runner path.

## Evidence Gates for Any Architecture Change

- A recommendation must cite a current file/line, test, command output, run dir, or measured timing.
- If evidence is a one-time local observation, label it as such and avoid using it as proof of a broad claim.
- Prefer internal seams over public API growth.
- Preserve current behavior first; optimize only after the exact bottleneck is measured.
- Claims about live T-FLEX behavior require live run evidence for that exact path.

## Risks

| Risk | Severity | Mitigation |
|---|---|---|
| `DocsIndex` can return stale local docs after `D:\REALPROJECTS\tflex_api` changes. | Medium | Gate on manifest/file freshness; expose index source/freshness metadata. |
| Runner splitting can become abstraction bloat. | Medium | Split only cache/store/orchestration responsibilities already present in `runner.py`; keep public use case unchanged. |
| Long-lived sessions can break isolation and reproducibility. | High | Keep stateless snippet execution as default; require explicit mode and run artifacts for any future session mode. |
| Recipe metadata can move drift from Python to Markdown/JSON. | Medium | Define freshness checks before migration; stale evidence must not report `verified=true`. |
| Undurable command observations can be mistaken for proof. | Medium | Attach future measurements to captured logs/run dirs or quote exact command output in the architecture note. |

## Open Questions

1. What latency threshold makes docs indexing worth implementing now?
2. Should `get_tflex_environment` later have cheap/full depth, or is full healthcheck rare enough?
3. What is the smallest recipe metadata format that enforces evidence freshness without process overhead?
4. Which result fields are contractual for `run_csharp_tflex` and must be protected by tests before runner refactor?
5. Should local developer bootstrap prefer `pip install -e .` or documented `$env:PYTHONPATH=src` for repo-root commands?

## Next Measurement Commands

Run only when the next round needs implementation evidence:

```powershell
$env:PYTHONPATH = Join-Path (Get-Location) 'src'

Measure-Command { python -m tflex_harness.cli search "TFlex.Model.Document" --scope symbols --limit 20 | Out-Null }
Measure-Command { python -m tflex_harness.cli search "TFlex.Model.Document" --scope types --limit 20 | Out-Null }
Measure-Command { python -m tflex_harness.cli search "TFlex.Model.Document" --scope chm --limit 20 | Out-Null }
Measure-Command { python -m tflex_harness.cli search "TFlex.Model.Document" --scope all --limit 20 | Out-Null }

Measure-Command { python -m tflex_harness.cli env | Out-Null }
Measure-Command { python -m tflex_harness.cli recipes | Out-Null }
Measure-Command { python -m tflex_harness.cli run-csharp --mode compile_only --artifact-prefix arch_measure_compile --code 'public class Program { public static int Main(){ return 0; } }' | Out-Null }
Measure-Command { python -m tflex_harness.cli run-csharp --mode compile_only --artifact-prefix arch_measure_compile_warm --code 'public class Program { public static int Main(){ return 0; } }' | Out-Null }
```
