# helper_assembly_build_backlog

## Live Verification Report

Test: `python -m tflex_harness.cli run-recipe helper_assembly_build_backlog --timeout-sec 120`

Docs used: `goal.md`; verified Fragment3D + PointsLCS path from existing helper recipes; local T-FLEX API docs for `Document3D.GetMates` and `Application.RunSystemCommand` shape.

Snippet: `agent_workspace/recipes/helper_assembly_build_backlog.cs`

Result: passed live in T-FLEX CAD 17.

Evidence:

- Run: `artifacts/runs/20260527_110934_645111_recipe_helper_assembly_build_backlog`
- `assemblyBuild.part.endChanges=OK`
- `assembly.endChanges=OK`
- `assemblyBacklog.summary.fragmentCount=3`
- `assemblyBacklog.summary.floatingFragmentCount=1`
- `assemblyBacklog.summary.collisionCount=1`
- `assemblyBacklog.summary.policyViolationCount=1`
- `mateInspector.mateCount=0`
- `mateInspector.graphExists=True`
- `commandProbe.listKnownCommands.available=False`
- `assemblyBacklog.expectedDetected=True`
- Artifacts include part `.grb`, assembly `.grb`, mate graph JSON, and validation summary JSON.

Blockers: positive native `MateEdgeCount>0` still needs a real native-mate `.grb`; this recipe proves inspector on a no-mate generated assembly only.
