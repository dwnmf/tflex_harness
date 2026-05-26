# Recipe: helper_assembly_validation

## Purpose

Create live T-FLEX assemblies and validate two assembly correctness gates:

- exact body collision detection using `Operation.Geometry.AABoundBox` broad phase plus `BaseBody.Clash(...)`;
- floating fragment detection using `Fragment3D.Fixing` and `Fragment3D.TargetLCS`.

This is now exact for solid body pairs reached through `Operation.Geometry.Solid[index]`. AABB is only a broad phase filter.

## Documentation Evidence

Docs used:

- `P:TFlex.Model.Model3D.Operation.GeometryData.AABoundBox`
- `P:TFlex.Model.Model3D.Geometry.ModelBodies.default(System.Int32)`
- `M:TFlex.Model.Model3D.Geometry.BaseBody.Clash(TFlex.Model.Model3D.Geometry.BaseBody,System.Boolean,System.Boolean)`
- `P:TFlex.Model.Model3D.Geometry.BaseClashResultItem.Type`
- `T:TFlex.Model.Model3D.Geometry.BaseBody.TypeOfClash`
- `P:TFlex.Model.Model3D.Fragment3D.Fixing`
- `F:TFlex.Model.Model3D.Fragment3D.FixingType.NoFixing`
- `P:TFlex.Model.Model3D.Fragment3D.SourceLCSName`
- `P:TFlex.Model.Model3D.Fragment3D.TargetLCS`
- `M:TFlex.Model.Model3D.Fragment3D.FixByFragmentLCS(System.String,TFlex.Model.Model3D.LCS)`

Live compile proved `Operation.Geometry.Solid[0]` returns `BaseBody`; `Operation.Geometry.Solid.Current` is `object`. `BaseBody.Clash(...)` is used instead of obsolete `ClashBody(...)`.

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

Run: `artifacts/runs/20260526_230853_507662_recipe_helper_assembly_validation`

Result: recipe passed with `assemblyValidation.live=True`.

Blockers: mate graph/BFS and DOF analysis are not implemented yet.

Evidence:

- bad assembly: `bad.pair.0_1.solid.0_0.clash.0.type=Interfere`, `bad.summary.clashPairCount=1`, `bad.summary.collisionCount=1`, `bad.summary.floatingFragmentCount=1`, `bad.expectedDetected=True`;
- good assembly: `good.summary.bboxOverlapCount=0`, `good.summary.collisionCount=0`, `good.summary.floatingFragmentCount=0`, `good.expectedClean=True`;
- LCS placement unit sanity: second good fragment bbox `good.body.1.bboxMinMm=50,-10,-20`, `good.body.1.bboxMaxMm=70,10,20`;
- final: `assemblyValidation.live=True`.

Artifacts:

- `assembly_validation_source_part.grb`
- `assembly_validation_bad.grb`
- `assembly_validation_good.grb`

## Limitations

- Collision is exact for solid body pairs via `BaseBody.Clash(...)`; AABB is only broad phase.
- Floating detection is LCS/fixing based. It is not yet a full mate graph BFS.
- Contacts are counted when `BaseBody.TypeOfClash.Abutment` is returned.
