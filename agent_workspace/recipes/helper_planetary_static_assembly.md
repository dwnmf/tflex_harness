# Recipe: helper_planetary_static_assembly

## Purpose

Create the simplified planetary gear `.grb` and STEP assembly from the prompt using visible C# helper source libraries.

This version uses `TFlexEasyGears.cs` direct-XY gear profiles, explicit tooth phases, and clearanced trapezoid teeth so the planet gears are visible at R42 and the simplified teeth do not visually collide.

## Documentation Evidence

Docs used:

- `D:\REALPROJECTS\tflex_api\llm\symbols.jsonl`
- `P:TFlex.Model.Document.ExportToSTEP` and `M:TFlex.Model.ExportToSTEP.Export(System.String)` for STEP export.
- `T:TFlex.Model.Model3D.ThickenExtrusion` and `F:TFlex.Model.Model3D.ThickenExtrusion.LengthValue.ValueNo` for exact one-sided extrusion.
- Existing verified session pattern from `.agents/skills/tflex-harness/SKILL.md`.
- Helper source set `all`, including `src/tflex_harness/csharp_helpers/TFlexEasyGears.cs`.

## C# Source

Snippet: `agent_workspace/recipes/helper_planetary_static_assembly.cs`

This recipe compiles with helper source set `all` from `src/tflex_harness/csharp_helpers`.

## Live Verification Report

Test: `helper_planetary_static_assembly`

Docs used:

- `D:\REALPROJECTS\tflex_api\llm\symbols.jsonl`
- Local helper source evidence in `src/tflex_harness/csharp_helpers`.

Snippet: `agent_workspace/recipes/helper_planetary_static_assembly.cs`

Result: pass.

Evidence:

- live run directory: `artifacts/runs/20260525_124700_025877_recipe_helper_planetary_static_assembly`;
- helper source files were copied into the run directory and recorded with SHA256 hashes, including `TFlexEasyGears.cs`;
- stdout evidence: `operations=9`; `phase.sunDeg=-7.5`; `phase.ringDeg=-3`; `planet_1/2/3.bboxCenterRadiusMm=42`; `mesh.sunRadialClearanceMm=0.5`; `mesh.ringRadialClearanceMm=0.5`; `contractFailCode=0`;
- artifact evidence: `helper_planetary_static_assembly.grb` size `638300` bytes and `helper_planetary_static_assembly.step` size `1955262` bytes;
- run returned exit code `0` in the verified local T-FLEX CAD 17 environment.

Additional reopen evidence:

- reopen run directory: `artifacts/runs/20260525_124340_928668_verify_planetary_helper_reopen_clearanced`;
- stdout evidence after opening the saved `.grb`: `reopen.operations=9`; `reopen.planetCount=3`; all three `reopen.*.centerRadiusMm=42`; `reopen.fail=0`;
- note: the reopen probe printed successful geometry evidence but the external process ended with T-FLEX/runtime exit `3762504530`, so use the generation run above as the pass/fail recipe evidence.

Blockers: none for generation/export on the verified local T-FLEX CAD 17 environment.

## Assumptions

- T-FLEX CAD 17 is installed locally and can initialize a 3D session.
- Helper source set `all` is available under `src/tflex_harness/csharp_helpers`.
- STEP export success is determined by a non-empty file artifact because `ExportToSTEP.Export` can return `False` while producing a valid non-empty STEP file in live evidence.
- Simplified teeth are schematic trapezoids, not true involute gears.

## Limitations

- This recipe validates helper-backed API paths, body count, dimensions, phases, radial clearances, and artifacts; it does not replace detailed engineering tooth-contact analysis.
- Output artifacts are written under the per-run `TFLEX_HARNESS_ARTIFACTS_DIR` through `EasySession.ArtifactPath`.

