# Recipe: helper_assembly_validation

## Purpose

Create live T-FLEX assemblies and validate assembly correctness gates:

- exact body collision detection using `Operation.Geometry.AABoundBox` broad phase plus `BaseBody.Clash(...)`;
- floating fragment detection using `Fragment3D.Fixing`, `Fragment3D.TargetLCS`, and native mate operation links;
- native mate enumeration through `Document3D.GetMates(doc)` for future graph/BFS work.

AABB is only a broad phase filter. Solid collision is checked exactly through `BaseBody.Clash(...)`.

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
- `M:TFlex.Model.Model3D.Document3D.GetMates(TFlex.Model.Document)`
- `P:TFlex.Model.Model3D.Mate.Operation1`
- `P:TFlex.Model.Model3D.Mate.Operation2`
- `P:TFlex.Model.Model3D.Mate.Element1`
- `P:TFlex.Model.Model3D.Mate.Element2`
- `P:TFlex.Model.Model3D.Mate.Type`
- `P:TFlex.Model.Model3D.Mate.Suppressed`

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

Run: `artifacts/runs/20260526_231540_012426_recipe_helper_assembly_validation`

Result: recipe passed with `assemblyValidation.live=True`.

Blockers: positive native mate-edge classification is not live-proven yet; simple LCS plane mate creation failed with `CompleteError` in `artifacts/runs/20260526_231412_287906_probe_create_lcs_mate`.

Evidence:

- bad assembly: `bad.pair.0_1.solid.0_0.clash.0.type=Interfere`, `bad.summary.clashPairCount=1`, `bad.summary.collisionCount=1`, `bad.summary.floatingFragmentCount=1`, `bad.expectedDetected=True`;
- bad floating reason: `bad.fragment.1.connectedByMate=False`, `bad.fragment.1.reason=no_lcs_fixing_or_mate`;
- bad mate summary: `bad.summary.mateCount=0`, `bad.summary.mateEdgeCount=0`, `bad.summary.mateOperationLinkCount=0`, `bad.summary.mateLinkedFragmentCount=0`;
- good assembly: `good.summary.bboxOverlapCount=0`, `good.summary.collisionCount=0`, `good.summary.floatingFragmentCount=0`, `good.expectedClean=True`;
- good mate summary: `good.summary.mateCount=0`, `good.summary.mateLinkedFragmentCount=0`;
- LCS placement unit sanity: second good fragment bbox `good.body.1.bboxMinMm=50,-10,-20`, `good.body.1.bboxMaxMm=70,10,20`;
- final: `assemblyValidation.live=True`.

Artifacts:

- `assembly_validation_source_part.grb`
- `assembly_validation_bad.grb`
- `assembly_validation_good.grb`

## Limitations

- Collision is exact for solid body pairs via `BaseBody.Clash(...)`; AABB is only broad phase.
- Mate enumeration is live-proven for this zero-mate recipe, but positive native mate-edge classification is not live-proven yet.
- Simple native mate creation between two LCS planes failed with `CompleteError` in `artifacts/runs/20260526_231412_287906_probe_create_lcs_mate`.
- Contacts are counted when `BaseBody.TypeOfClash.Abutment` is returned, but a contact-specific live case remains pending.
