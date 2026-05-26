# Recipe: helper_assembly_validation

## Purpose

Create live T-FLEX assemblies and validate assembly correctness gates:

- exact body collision detection using `Operation.Geometry.AABoundBox` broad phase plus `BaseBody.Clash(...)`;
- floating fragment detection using `Fragment3D.Fixing`, `Fragment3D.TargetLCS`, and native mate operation links;
- face-contact/tolerance-contact classification that does not false-fail as collision;
- DOF-lite groundedness and estimated constraint counting;
- native mate enumeration through `Document3D.GetMates(doc)` for future graph/BFS work.

AABB is used in two ways:

- strict `BoxesOverlap(...)` detects volume-overlap candidates;
- inclusive `BoxesMayTouchOrOverlap(...)` includes face contacts for exact kernel checking.

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

Run: `artifacts/runs/20260526_233717_009768_recipe_helper_assembly_validation`

Result: recipe passed with `assemblyValidation.live=True`.

Blockers: positive native mate-edge classification is not live-proven yet; simple LCS plane mate creation failed with `CompleteError` in `artifacts/runs/20260526_231412_287906_probe_create_lcs_mate`. Installed prototype scan `artifacts/runs/20260526_232731_135336_probe_scan_prototype_mates` opened 50 `.grb` prototypes and found `scan.withMates=0`.

Evidence:

- bad assembly: `bad.pair.0_1.solid.0_0.clash.0.type=Interfere`, `bad.summary.clashPairCount=1`, `bad.summary.collisionCount=1`, `bad.summary.floatingFragmentCount=1`, `bad.expectedDetected=True`;
- bad floating/DOF reason: `bad.fragment.1.connectedByMate=False`, `bad.fragment.1.reason=no_lcs_fixing_or_mate`, `bad.fragment.1.estimatedRemainingDof=6`, `bad.summary.estimatedDofRemaining=6`;
- good assembly: `good.summary.broadPhasePairCount=0`, `good.summary.collisionCount=0`, `good.summary.floatingFragmentCount=0`, `good.summary.fullyConstrainedFragmentCount=2`, `good.summary.estimatedDofRemaining=0`, `good.expectedClean=True`;
- touching assembly: `touch.pair.0_1.bboxOverlap=False`, `touch.pair.0_1.broadPhaseCandidate=True`, `touch.pair.0_1.solid.0_0.clash.0.type=Interfere`, `touch.pair.0_1.solid.0_0.clash.0.classification=contact_by_bbox_no_volume_overlap`, `touch.summary.collisionCount=0`, `touch.summary.contactCount=1`, `touch.summary.estimatedDofRemaining=0`, `touch.expectedContact=True`;
- mate summary: `bad.summary.mateCount=0`, `good.summary.mateCount=0`, `touch.summary.mateCount=0`;
- final: `assemblyValidation.live=True`.

Artifacts:

- `assembly_validation_source_part.grb`
- `assembly_validation_bad.grb`
- `assembly_validation_good.grb`
- `assembly_validation_touching.grb`

## Limitations

- Collision is exact for solid body pairs via `BaseBody.Clash(...)`; AABB is only broad phase.
- Touching faces are classified as contact when strict AABB volume overlap is false, even if the kernel reports `Interfere`.
- Mate enumeration is live-proven for zero-mate generated assemblies. Positive native mate-edge classification needs a real native-mate `.grb` or a working creation recipe.
- DOF-lite is an estimate: 6 DOF per fragment, LCS fixing removes 6, native mate types remove approximate counts when real mate edges exist. It is not a full geometric constraint rank solver.
