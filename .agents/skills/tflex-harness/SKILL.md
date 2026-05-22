---
name: tflex-harness
description: "Work on the local D:\\REALPROJECTS\\tflex_harness repository: T-FLEX CAD 17 harness/MCP code, C# snippet runner, recipes, live CAD validation, artifacts, diagnostics, and project documentation. Use this when editing, testing, debugging, or operating tflex-harness itself. Communicate in a concise caveman style while preserving exact commands, paths, and evidence."
---

# T-FLEX Harness

## Voice

Use caveman style for user-facing text:
- Short sentences. Direct words. No fluff.
- Prefer: “Me check. Me run tests. Result good.”
- Still keep technical names exact: paths, commands, APIs, file names, errors.
- Do not hide uncertainty. Say “Not know yet” or “Need live T-FLEX.”

## Repo Map

- Root: `D:\REALPROJECTS\tflex_harness`
- Main package: `src/tflex_harness`
- Tests: `tests/unit`, `tests/smoke`, `tests/integration`
- Local skills: `.agents/skills`
- Generated runs: `artifacts/runs`
- Generated T-FLEX files: `artifacts/tflex_docs`
- Snippet candidates: `agent_workspace/snippets`
- Event log: `logs/events.jsonl`
- Architecture/status: `goal.md`
- T-FLEX API docs: `D:\REALPROJECTS\tflex_api\llm`

## Core Rules

1. Check `git status --short` before tracked edits.
2. Keep generated artifacts out of commits unless user asks.
3. Use exact search first: `rg`, `fff`, or local docs grep.
4. For T-FLEX API behavior, also use `deepwiki-tflex-api`.
5. Prefer smallest validation:
   - Unit/smoke for harness code.
   - `compile_only` before live CAD when API shape uncertain.
   - Live run only when needed.
6. For live snippets, capture run dir and stdout evidence.
7. If snippet prints success but process times out, inspect `result.json`, `stdout.txt`, saved `.grb`, and stale `Snippet` process before judging failure.

## Useful Commands

```powershell
python -m pytest tests/unit -v
python -m pytest tests/smoke -v
python -m tflex_harness.cli env
python -m tflex_harness.cli search "TFlex.Model.Document" --limit 5
python -m tflex_harness.cli recipes
python -m tflex_harness.cli state
python -m tflex_harness.cli run-csharp --mode compile_only --code "public class Program { public static int Main(){ return 0; } }"
```

MCP entrypoint:

```powershell
tflex-harness-mcp
```

## Live C# Snippet Pattern

Use visible C# code. Pick explicit references:

- `TFlexAPI` for 2D/document API.
- `TFlexAPI3D` for 3D operations.
- `TFlexCommandAPI` only for command/UI API.
- `TFlexAPIData` only for data API.

For direct Python runner calls:

```powershell
$env:PYTHONPATH = Join-Path (Get-Location) 'src'
@'
from tflex_harness.runner import run_csharp_snippet
result = run_csharp_snippet(
    code='public class Program { public static int Main(){ System.Console.WriteLine("ok"); return 0; } }',
    mode='run',
    timeout_sec=30,
    references=[],
    artifact_prefix='manual_probe',
)
print(result)
'@ | python -
```

## Validation Ladder

For harness code changes:
1. Run targeted unit test.
2. Run related smoke test.
3. Run integration only if live T-FLEX is required and user scope allows.

For T-FLEX API snippets:
1. Search `D:\REALPROJECTS\tflex_api\llm\symbols.jsonl`.
2. Open matching `llm/types/*.md`.
3. Compile with `mode='compile_only'`.
4. Run live if compile passes.
5. Save outputs under `artifacts/tflex_docs` or the snippet run dir.

## Live 3D API Notes

Use these findings when generating or debugging 3D snippets:

- Create document `Variable` objects in their own `doc.BeginChanges(...)` / `doc.EndChanges()` block before geometry that references them. Mixing variable creation and dependent 3D operations in one changes block can yield `CompleteError` and disposed-object errors.
- T-FLEX variable trigonometry uses degrees for `sin(Angle)` and `cos(Angle)`. Do not convert `Angle` to radians unless live evidence says otherwise.
- For simple parametric 3D solids, prefer `TFlex.Model.Model3D.Block` and `TFlex.Model.Model3D.Cylinder`.
- For 3D object placement, use `Object3D.Transformations.AddBaseTransfGroup()` with:
  - `TransformationGroup.AddMoveTransf(TransformationCoordinate.X/Y/Z, Parameter)`
  - `TransformationGroup.AddRotateTransf(TransformationCoordinate.X/Y/Z, Parameter)`
- Do not use `Object3D.VolatileTransformations` for new snippets. In live T-FLEX CAD 17 it can throw: `Property VolatileTransformation is obsolete. Use Transformations property instead`.
- `Document3D.GetMates(document)` and `Mate` exist, but native `Mate` creation is fragile. `Mate.Element1/Element2` can be set to `Geometry.Axis`/other geometry, yet live runs may return `CompleteError` and no mate. Treat native assembly mates as unverified until a live snippet proves the exact geometry pair.
- If a user asks for assembly constraints and native `Mate` fails, report clearly: parametric kinematics via variables/transformation groups verified; native `Mate` objects not verified.

## Reporting

Report in caveman style with evidence:

- `Changed`: files touched.
- `Verified`: exact commands or run dirs.
- `Not verified`: live CAD gaps, timeouts, skipped tests.

Example:

```text
Done. Me add recipe.

Changed:
- `src/tflex_harness/recipes.py`

Verified:
- `python -m pytest tests/unit/test_recipes.py -v`

Not verified:
- Live T-FLEX. Not needed.
```
