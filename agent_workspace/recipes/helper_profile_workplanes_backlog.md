# helper_profile_workplanes_backlog

## Live Verification Report

Test: `python -m tflex_harness.cli run-recipe helper_profile_workplanes_backlog --timeout-sec 120`

Docs used: `goal.md`; local T-FLEX API docs; existing verified export/workplane facts.

Snippet: `agent_workspace/recipes/helper_profile_workplanes_backlog.cs`

Result: passed live in T-FLEX CAD 17.

Evidence:

- Run: `artifacts/runs/20260527_111707_207555_recipe_helper_profile_workplanes_backlog`
- `profiles.endChanges=OK`
- `workplane.top.profileAxes=X,Y`; `workplane.top.extrudeAxis=Z`
- `workplane.front.profileAxes=X,Z`; `workplane.front.extrudeAxis=Y`
- `workplane.left.profileAxes=Y,Z`; `workplane.left.extrudeAxis=X`
- `profiles.created=24`
- `profiles.operations=24`
- `profiles.validBbox=24`
- `profiles.positiveBbox=24`
- `profiles.expectedOperations.ok=True`
- `easy.grbExists=True`
- `profiles.expectedClean=True`

Blockers: none for this recipe. Some bodies rejected direct `Name` assignment; `EasySolids.TrySetName` caught it and modeling continued.
