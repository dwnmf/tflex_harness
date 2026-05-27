# Current Focus: Assembly Validation MVP

## Contents
- Live-proven state
- Important assembly validation facts
- Next work and do-not-rerun rule

## Current Focus: Assembly Validation MVP

As of 2026-05-26, active `goal.md` is assembly validation.

Live-proven now:

- Helper source: `src/tflex_harness/csharp_helpers/TFlexEasyAssemblyValidation.cs`.
- Helper set: `easy_assembly_validation`.
- Recipe: `agent_workspace/recipes/helper_assembly_validation.cs`.
- Live run: `artifacts/runs/20260526_233717_009768_recipe_helper_assembly_validation`.
- Command: `python -m tflex_harness.cli run-recipe helper_assembly_validation --timeout-sec 120`.
- Bad assembly evidence: `bad.pair.0_1.solid.0_0.clash.0.type=Interfere`, `bad.summary.clashPairCount=1`, `bad.summary.collisionCount=1`, `bad.summary.floatingFragmentCount=1`, `bad.fragment.1.reason=no_lcs_fixing_or_mate`, `bad.fragment.1.estimatedRemainingDof=6`, `bad.expectedDetected=True`.
- Good assembly evidence: `good.summary.broadPhasePairCount=0`, `good.summary.collisionCount=0`, `good.summary.floatingFragmentCount=0`, `good.summary.mateCount=0`, `good.summary.fullyConstrainedFragmentCount=2`, `good.summary.estimatedDofRemaining=0`, `good.expectedClean=True`.
- Touching evidence: `touch.pair.0_1.solid.0_0.clash.0.classification=contact_by_bbox_no_volume_overlap`, `touch.summary.collisionCount=0`, `touch.summary.contactCount=1`, `touch.summary.estimatedDofRemaining=0`, `touch.expectedContact=True`.
- Final evidence: `assemblyValidation.live=True`.

Important facts:

- Collision now uses inclusive AABB broad phase via `Operation.Geometry.AABoundBox`, then exact `BaseBody.Clash(...)`. Strict AABB volume overlap separates collision from face contact.
- DOF-lite counts 6 DOF per `Fragment3D`; LCS-fixed fragments get 6 constraints and remaining DOF 0; no-fixing fragments remain 6 DOF.
- Mate inspector uses `Document3D.GetMates(doc)` and logs `Mate.Operation1/2`, `Element1/2`, `Type`, `Suppressed`; mate edges have approximate constraint counts when present.
- Live compile fact: `Operation.Geometry.Solid[index]` returns `BaseBody`; `Operation.Geometry.Solid.Current` is only `object`.
- Do not use obsolete `BaseBody.ClashBody(...)`; compiler warns to use `Clash(...)`.
- Not verified yet: positive native mate-edge case with `MateEdgeCount>0`; simple LCS plane mate probe failed with `CompleteError` in `artifacts/runs/20260526_231412_287906_probe_create_lcs_mate`; installed prototype scan `artifacts/runs/20260526_232731_135336_probe_scan_prototype_mates` found `scan.withMates=0`.
- Next work: find/create real native mate assembly, then BFS/DOF analysis.

Do not rerun broad prototype/document batches for this goal. Use only targeted live recipe/probes.
