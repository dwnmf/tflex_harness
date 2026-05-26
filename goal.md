# T-FLEX Harness Goal: Assembly Validation

Date: 2026-05-26

Current objective: production-ready MVP for assembly validation through `tflex_harness` helpers.

Failure classes in scope:

1. bodies/fragments placed inside each other;
2. `Fragment3D` objects floating without LCS/fixing/mate connection;
3. face-contact/tolerance-contact that must not become a false collision;
4. DOF-lite groundedness and constraint counting;
5. native mate graph evidence for future BFS/DOF checks.

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

Run: `artifacts/runs/20260526_233717_009768_recipe_helper_assembly_validation`

Evidence:

- bad assembly has exact solid collision:
  - `bad.summary.broadPhasePairCount=1`
  - `bad.summary.bboxOverlapCount=1`
  - `bad.pair.0_1.solid.0_0.clash.0.type=Interfere`
  - `bad.summary.clashPairCount=1`
  - `bad.summary.collisionCount=1`
  - `bad.expectedDetected=True`
- bad assembly has one floating/underconstrained fragment:
  - `bad.fragment.1.fixing=NoFixing`
  - `bad.fragment.1.targetLcsNull=True`
  - `bad.fragment.1.connectedByMate=False`
  - `bad.fragment.1.reason=no_lcs_fixing_or_mate`
  - `bad.fragment.1.estimatedRemainingDof=6`
  - `bad.summary.floatingFragmentCount=1`
  - `bad.summary.groundedFragmentCount=1`
  - `bad.summary.ungroundedFragmentCount=1`
  - `bad.summary.estimatedDofRemaining=6`
- good assembly is clean and fully constrained by LCS fixing:
  - `good.summary.broadPhasePairCount=0`
  - `good.summary.collisionCount=0`
  - `good.summary.floatingFragmentCount=0`
  - `good.summary.groundedFragmentCount=2`
  - `good.summary.fullyConstrainedFragmentCount=2`
  - `good.summary.estimatedDofRemaining=0`
  - `good.expectedClean=True`
- touching assembly is contact, not collision:
  - `touch.pair.0_1.bboxOverlap=False`
  - `touch.pair.0_1.broadPhaseCandidate=True`
  - `touch.pair.0_1.solid.0_0.clash.0.type=Interfere`
  - `touch.pair.0_1.solid.0_0.clash.0.classification=contact_by_bbox_no_volume_overlap`
  - `touch.summary.bboxContactCandidateCount=1`
  - `touch.summary.collisionCount=0`
  - `touch.summary.contactCount=1`
  - `touch.summary.groundedFragmentCount=2`
  - `touch.summary.estimatedDofRemaining=0`
  - `touch.expectedContact=True`
- native mate inspector runs live:
  - `bad.summary.mateCount=0`
  - `good.summary.mateCount=0`
  - `touch.summary.mateCount=0`
- final pass: `assemblyValidation.live=True`.

## Important API Facts

- Body envelope: `Operation.Geometry.AABoundBox` for broad phase.
- Exact body access: `Operation.Geometry.Solid[index]` returns `BaseBody`.
- Exact clash: `BaseBody.Clash(BaseBody, false, true)` returns `ICollection<BaseClashResultItem>`.
- Exact collision type live-proven: `BaseBody.TypeOfClash.Interfere`.
- Face contact can be returned by the kernel as `Interfere`; helper classifies it as contact when strict AABB volume overlap is false.
- Broad phase is inclusive-with-tolerance for exact checks, but strict `BoxesOverlap(...)` still separates volume overlap from face contact.
- Fragment fixing/connectivity signals:
  - `Fragment3D.Fixing`
  - `Fragment3D.FixingType.NoFixing`
  - `Fragment3D.SourceLCSName`
  - `Fragment3D.TargetLCS`
  - `Fragment3D.FixByFragmentLCS(...)`
- DOF-lite/constraint counting:
  - each `Fragment3D` starts with 6 estimated DOF;
  - `FixByFragmentLCS(...)`/target LCS contributes 6 constraints and grounds the fragment;
  - native mate edges contribute estimated constraints by mate type when real `Mate.Operation1/2` edges exist;
  - BFS from LCS-fixed roots through mate edges computes grounded vs ungrounded fragments.
- Native mate enumeration:
  - `Document3D.GetMates(doc)` returns assembly mates.
  - `Mate.Operation1` and `Mate.Operation2` expose linked operations when available.
  - `Mate.Element1`, `Mate.Element2`, `Mate.Type`, and `Mate.Suppressed` compile and are logged.
- `CoordinateNode3D` LCS placement uses model units; recipe converts mm with `EasyUnits.MmToModel(...)`.

## Mate Status

Positive native mate-edge classification remains blocked by input data/API behavior, not by the validator hook:

- direct native mate creation probes returned `CompleteError`, including `artifacts/runs/20260526_231412_287906_probe_create_lcs_mate`;
- installed prototype scan opened 50 `.grb` prototypes and found no native mates: `artifacts/runs/20260526_232731_135336_probe_scan_prototype_mates`, `scan.opened=50`, `scan.withMates=0`;
- DeepWiki/local docs confirm the visible API shape (`new Mate(document)`, `Type`, `Element1`, `Element2`, `Document3D.GetMates(doc)`), but no working creation recipe is documented.

This is production-ready for generated/legacy assemblies where collisions, contacts, floating fragments, and LCS-based DOF-lite checks are the gates. It is still not a full geometric constraint rank solver and does not yet prove positive `MateEdgeCount>0` on a real native-mate file.

## Next Target

1. Obtain or create a real native-mate `.grb` and prove `MateEdgeCount>0`.
2. Prove mate-edge BFS/constraint counting on that real native-mate file.
3. Add policy options: fail on contact vs allow contact, allowed overlap pairs, ignored body names.

## Done Criteria For Current MVP

- Helper source exists and is registered: done.
- Recipe exists with markdown/metadata: done.
- Recipe compiles and runs live: done.
- Live stdout proves bad collision/floating case: done.
- Live stdout proves clean separated case: done.
- Live stdout proves face-contact is not false collision: done.
- Live stdout proves DOF-lite and constraint counting for LCS-fixed/floating fragments: done.
- Mate enumeration compiles and runs in live recipe: done.
- Installed prototypes scanned for positive mate file: done, none found.
- Positive mate-edge case: blocked until real native-mate input exists or working creation API is discovered.
- Commit and push: pending.
