# T-FLEX Harness Goal: Assembly Validation

Date: 2026-05-26

Current objective: live MVP for assembly validation through `tflex_harness` helpers.

Failure classes in scope:

1. bodies/fragments placed inside each other;
2. `Fragment3D` objects floating without LCS/fixing/mate connection;
3. native mate graph evidence for future BFS/DOF checks.

## What Is Implemented

- Visible helper source: `src/tflex_harness/csharp_helpers/TFlexEasyAssemblyValidation.cs`.
- Helper set: `easy_assembly_validation`.
- Verified recipe:
  - `agent_workspace/recipes/helper_assembly_validation.cs`
  - `agent_workspace/recipes/helper_assembly_validation.md`
  - `agent_workspace/recipes/helper_assembly_validation.recipe.json`

## Live-Proven Behavior

Command:

```powershell
$env:PYTHONPATH = Join-Path (Get-Location) 'src'
python -m tflex_harness.cli run-recipe helper_assembly_validation --timeout-sec 120
```

Run: `artifacts/runs/20260526_231540_012426_recipe_helper_assembly_validation`

Evidence:

- bad assembly has exact solid collision:
  - `bad.summary.bboxOverlapCount=1`
  - `bad.pair.0_1.solid.0_0.clash.0.type=Interfere`
  - `bad.summary.clashPairCount=1`
  - `bad.summary.collisionCount=1`
  - `bad.expectedDetected=True`
- bad assembly has one floating fragment:
  - `bad.fragment.1.fixing=NoFixing`
  - `bad.fragment.1.targetLcsNull=True`
  - `bad.fragment.1.connectedByMate=False`
  - `bad.fragment.1.reason=no_lcs_fixing_or_mate`
  - `bad.summary.floatingFragmentCount=1`
- good assembly is clean:
  - `good.summary.bboxOverlapCount=0`
  - `good.summary.collisionCount=0`
  - `good.summary.floatingFragmentCount=0`
  - `good.expectedClean=True`
- native mate inspector runs live:
  - `bad.summary.mateCount=0`
  - `bad.summary.mateEdgeCount=0`
  - `bad.summary.mateOperationLinkCount=0`
  - `good.summary.mateCount=0`
  - `good.summary.mateLinkedFragmentCount=0`
- final pass: `assemblyValidation.live=True`.

## Important API Facts

- Body envelope: `Operation.Geometry.AABoundBox` for broad phase.
- Exact body access: `Operation.Geometry.Solid[index]` returns `BaseBody`.
- Exact clash: `BaseBody.Clash(BaseBody, false, true)` returns `ICollection<BaseClashResultItem>`.
- Exact collision type live-proven: `BaseBody.TypeOfClash.Interfere`.
- Fragment fixing/connectivity signals:
  - `Fragment3D.Fixing`
  - `Fragment3D.FixingType.NoFixing`
  - `Fragment3D.SourceLCSName`
  - `Fragment3D.TargetLCS`
  - `Fragment3D.FixByFragmentLCS(...)`
- Native mate enumeration:
  - `Document3D.GetMates(doc)` returns assembly mates.
  - `Mate.Operation1` and `Mate.Operation2` expose linked operations when available.
  - `Mate.Element1`, `Mate.Element2`, `Mate.Type`, and `Mate.Suppressed` compile and are logged.
- `CoordinateNode3D` LCS placement uses model units; recipe converts mm with `EasyUnits.MmToModel(...)`.

## Known Limitation

Collision detection is exact for solid body pairs: AABB broad phase, then `Operation.Geometry.Solid[index]` -> `BaseBody.Clash(...)`. `ClashBody(...)` is obsolete and not used.

Floating detection now combines LCS/fixing state plus a native mate operation hook. Positive native mate-edge classification is not live-proven yet: simple LCS plane mate creation probe failed with `CompleteError` in `artifacts/runs/20260526_231412_287906_probe_create_lcs_mate`.

This is not yet a full DOF solver.

## Next Target

1. Find/create a live assembly with real native mates and prove `MateEdgeCount>0`.
2. Extend from mate operation hooks to BFS over LCS/mate links.
3. Add contact-specific live case for `BaseBody.TypeOfClash.Abutment`.

## Done Criteria For This Iteration

- Helper source exists and is registered: done.
- Recipe exists with markdown/metadata: done.
- Recipe compiles and runs live: done.
- Live stdout proves bad and good cases: done.
- Mate enumeration compiles and runs in live recipe: done.
- Positive mate-edge case: not done.
- Commit and push: pending.
