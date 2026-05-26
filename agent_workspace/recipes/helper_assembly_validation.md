# Recipe: helper_assembly_validation

## Purpose

Create live T-FLEX assemblies and validate two assembly correctness gates:

- body collision candidates using `Operation.Geometry.AABoundBox` in millimeters;
- floating fragment detection using `Fragment3D.Fixing` and `Fragment3D.TargetLCS`.

This is a fast live MVP. It is intentionally conservative: AABB overlap is reported as a collision candidate and can have false positives for sparse geometry. Exact kernel clash is not claimed yet.

## Documentation Evidence

Docs used:

- `P:TFlex.Model.Model3D.Operation.GeometryData.AABoundBox`
- `P:TFlex.Model.Model3D.Fragment3D.Fixing`
- `F:TFlex.Model.Model3D.Fragment3D.FixingType.NoFixing`
- `P:TFlex.Model.Model3D.Fragment3D.SourceLCSName`
- `P:TFlex.Model.Model3D.Fragment3D.TargetLCS`
- `M:TFlex.Model.Model3D.Fragment3D.FixByFragmentLCS(System.String,TFlex.Model.Model3D.LCS)`

Docs also expose `BaseBody.ClashBody(BaseBody)`, but live compile proved `Operation.Body`, `Operation.Geometry`, and `Operation.Geometry.Solid` do not expose that method directly in visible snippets. Next iteration can bridge this separately.

## C# Source

Snippet: `agent_workspace/recipes/helper_assembly_validation.cs`
Helper: `src/tflex_harness/csharp_helpers/TFlexEasyAssemblyValidation.cs`
Helper set: `easy_assembly_validation`

## Live Verification Report

Test: live T-FLEX run on 2026-05-26.

Command:

```powershell
$env:PYTHONPATH = Join-Path (Get-Location) 'src'
python -m tflex_harness.cli run-recipe helper_assembly_validation --timeout-sec 120
```

Run: `artifacts/runs/20260526_225737_199228_recipe_helper_assembly_validation`

Result: recipe passed with `assemblyValidation.live=True`.

Blockers: exact solid intersection is not bridged yet; current collision signal is AABB candidate detection.

Evidence:

- bad assembly: `bad.summary.bboxOverlapCount=1`, `bad.summary.collisionCount=1`, `bad.summary.floatingFragmentCount=1`, `bad.expectedDetected=True`;
- good assembly: `good.summary.bboxOverlapCount=0`, `good.summary.collisionCount=0`, `good.summary.floatingFragmentCount=0`, `good.expectedClean=True`;
- LCS placement unit sanity: second good fragment bbox `good.body.1.bboxMinMm=50,-10,-20`, `good.body.1.bboxMaxMm=70,10,20`;
- final: `assemblyValidation.live=True`.

Artifacts:

- `assembly_validation_source_part.grb`
- `assembly_validation_bad.grb`
- `assembly_validation_good.grb`

## Limitations

- Collision is currently AABB-based candidate detection, not exact solid intersection volume.
- Floating detection is LCS/fixing based. It is not yet a full mate graph BFS.
- Contacts are not classified until exact clash bridge is implemented.
