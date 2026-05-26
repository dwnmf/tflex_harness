# T-FLEX Harness Goal: Assembly Validation

Date: 2026-05-26

Current objective: live MVP for two assembly failure classes:

1. bodies/fragments placed inside each other;
2. `Fragment3D` objects floating without LCS/fixing connection.

## What Is Implemented

- New visible helper source: `src/tflex_harness/csharp_helpers/TFlexEasyAssemblyValidation.cs`.
- New helper set in runner: `easy_assembly_validation`.
- New verified recipe:
  - `agent_workspace/recipes/helper_assembly_validation.cs`
  - `agent_workspace/recipes/helper_assembly_validation.md`
  - `agent_workspace/recipes/helper_assembly_validation.recipe.json`

## Live-Proven Behavior

Command:

```powershell
$env:PYTHONPATH = Join-Path (Get-Location) 'src'
python -m tflex_harness.cli run-recipe helper_assembly_validation --timeout-sec 120
```

Run: `artifacts/runs/20260526_225737_199228_recipe_helper_assembly_validation`

Evidence:

- bad assembly has overlapping fragments:
  - `bad.summary.bboxOverlapCount=1`
  - `bad.summary.collisionCount=1`
  - `bad.expectedDetected=True`
- bad assembly has one floating fragment:
  - `bad.fragment.1.fixing=NoFixing`
  - `bad.fragment.1.targetLcsNull=True`
  - `bad.summary.floatingFragmentCount=1`
- good assembly is clean:
  - `good.summary.bboxOverlapCount=0`
  - `good.summary.collisionCount=0`
  - `good.summary.floatingFragmentCount=0`
  - `good.expectedClean=True`
- final pass: `assemblyValidation.live=True`.

## Important API Facts

- Body envelope: `Operation.Geometry.AABoundBox`.
- Fragment fixing/connectivity signals:
  - `Fragment3D.Fixing`
  - `Fragment3D.FixingType.NoFixing`
  - `Fragment3D.SourceLCSName`
  - `Fragment3D.TargetLCS`
  - `Fragment3D.FixByFragmentLCS(...)`
- `CoordinateNode3D` LCS placement uses model units; recipe converts mm with `EasyUnits.MmToModel(...)`.

## Known Limitation

Collision detection is currently AABB-based candidate detection. It is fast and live-proven, but not exact solid intersection. Local docs expose `BaseBody.ClashBody(BaseBody)`, but live compile showed `Operation.Body`, `Operation.Geometry`, and `Operation.Geometry.Solid` do not expose that method directly from visible snippets. Exact clash bridge is next work, not claimed done.

Floating detection is LCS/fixing based. It is not yet a full mate graph BFS/DOF solver.

## Next Target

1. Find a live-compiling bridge from model operations/fragments to `BaseBody.ClashBody(...)`, or another exact kernel intersection API.
2. Promote AABB overlap to broad phase only once exact clash is bridged.
3. Extend floating analysis from simple LCS/fixing state to mate graph traversal when mate API is located and live-proven.

## Done Criteria For This Iteration

- Helper source exists and is registered: done.
- Recipe exists with markdown/metadata: done.
- Recipe compiles and runs live: done.
- Live stdout proves bad and good cases: done.
- README and skill updated: done in this iteration.
- Commit and push: pending.
