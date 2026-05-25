# T-FLEX Harness Architecture

Date: 2026-05-24. Scope: architecture note; no production code changes.

## Purpose

`tflex_harness` is a thin, evidence-driven harness around the real T-FLEX CAD 17 API. It helps an agent search local API docs, write visible C# snippets, compile/run them, inspect diagnostics/artifacts, and promote proven recipes. It must not become a replacement T-FLEX SDK or a broad CAD wrapper framework.

## Consensus Decisions

1. **Python is the control plane.** Python owns MCP/CLI transport, documentation search, diagnostics, process execution, run/artifact storage, logs, and recipe registry glue.
2. **C# is the execution boundary.** CAD API work happens through visible C# snippets or recipes compiled against the real `TFlexAPI*.dll` assemblies.
3. **The public MCP surface stays small.** Preserve the docs/run/observe loop: search docs, inspect environment/state, compile/run C#, list/run verified recipes, and save snippet candidates.
4. **Internal seams already exist.** `DocsIndex`, `RunStore`, `CompileCache`, `SnippetRunner`, and `RecipeRegistry` are current code boundaries. Future work may refine or extract them only with contract snapshots, tests, and measurement evidence.
5. **Evidence beats abstraction.** Add public CAD-specific tools or new execution modes only after current snippets/recipes prove insufficient.

## Evidence Baseline

- `README.md:5` states the intended split: Python is the thin control plane; C# is used for typed snippets against the real T-FLEX CAD 17 .NET API.
- `README.md:25`-`README.md:31` lists the current public MCP/CLI tools and supports keeping the public surface small.
- `goal.md:5`, `goal.md:13`, `goal.md:18`, `goal.md:45`-`goal.md:54`, and `goal.md:63` define a thin, verifiable harness rather than a wrapper SDK.
- `src/tflex_harness/mcp_server.py:24`-`src/tflex_harness/mcp_server.py:46` shows MCP functions as thin forwarding adapters.
- Existing internal seams are present at `src/tflex_harness/docs_search.py:79`, `src/tflex_harness/runner.py:122`, `src/tflex_harness/runner.py:151`, `src/tflex_harness/runner.py:162`, and `src/tflex_harness/recipes.py:72`.
- `architecture.md` is currently empty in the worktree and must be reconstructed from the agreed draft, not accepted as-is.

## Existing Internal Seams

| Seam | Current location | Boundary rule |
|---|---|---|
| `DocsIndex` | `src/tflex_harness/docs_search.py:79` | Local docs indexing/search support. Keep exact local evidence; do not replace with semantic-only retrieval without measurements. |
| `RunStore` | `src/tflex_harness/runner.py:122` | Own run directories, request/result persistence, and run evidence shape. |
| `CompileCache` | `src/tflex_harness/runner.py:151` | Own content-hash build reuse while keeping cache hit/miss observable. |
| `SnippetRunner` | `src/tflex_harness/runner.py:162` | Orchestrate visible C# compile/run without hiding source behind opaque CAD commands. |
| `RecipeRegistry` | `src/tflex_harness/recipes.py:72` | Own verified recipe discovery/execution metadata; verification must not drift from source/evidence. |

## User Loop And Invariants

- User loop: search docs -> write visible C# -> compile/run -> observe diagnostics/artifacts -> refine -> promote verified recipe.
- Snippet and recipe source remains visible and persisted with run evidence.
- Compile errors, runtime errors, T-FLEX exceptions, timeouts, stdout/stderr, result JSON, and generated artifacts remain observable.
- Refactors preserve existing CLI/MCP contracts unless a separate evidence-backed decision changes them.
- Live T-FLEX behavior claims require live run evidence for the exact path being claimed.

## Non-Goals

- No broad Python CAD object model or wrapper SDK.
- No public `create_line`, `create_extrusion`, `make_drawing`, or similar CAD-specific MCP tool family.
- No hidden Python/COM automation path as the primary execution route.
- No long-lived T-FLEX session as the default execution mode.
- No database, service, or semantic-only docs system unless measured local-doc latency justifies it.

## Evidence Gates For Future Changes

- Every architecture recommendation cites a current file/line, command output, test, run dir, or measured timing.
- Prefer internal seam refinement over public API growth.
- Before changing `DocsIndex`, measure cold/warm search latency by scope and prove current behavior is a material delay or maintenance problem.
- Before changing runner seams, capture current `run-csharp` result fields, run-dir files, cache behavior, and targeted tests.
- Before changing recipe metadata, define freshness fields such as source hash, evidence run id, `last_verified`, limitations, and stale-evidence behavior.
- Before adding any long-lived T-FLEX session mode, prove the exact isolation, cleanup, artifact, and reproducibility contract.

## Risks

| Risk | Severity | Mitigation |
|---|---|---|
| Public CAD wrapper tools hide real API details and recreate a brittle SDK. | High | Keep C# snippets/recipes as the execution boundary. |
| Existing seams get over-extracted into abstraction bloat. | Medium | Refine only when contract snapshots, tests, or measurements show pressure. |
| Docs indexing returns stale local API evidence. | Medium | Tie index freshness to source files/manifests and expose freshness metadata. |
| Recipe metadata drifts from source or live evidence. | Medium | Require source/evidence freshness checks before reporting `verified=true`. |
| Long-lived sessions weaken isolation and reproducibility. | High | Keep stateless snippet execution as default; require explicit evidence for any alternate mode. |
| Empty `architecture.md` is accepted accidentally. | High | Write back the consensus draft and verify the file is non-empty. |

## Open Questions

1. What measured docs-search latency threshold justifies changing `DocsIndex`?
2. Which `run_csharp_tflex` result fields are contractual and need tests before runner changes?
3. What is the smallest recipe metadata format that proves freshness without process overhead?
4. Should environment/state probes later support cheap/full depth, or is current behavior sufficient?
