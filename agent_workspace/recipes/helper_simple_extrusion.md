# Recipe: helper_simple_extrusion

## Purpose

Create a 20 mm diameter, 8 mm thick extrusion through helper source and save GRB evidence.

## Documentation Evidence

Docs used:

- `D:\REALPROJECTS\tflex_api\llm\symbols.jsonl`
- `P:TFlex.Model.Document.ExportToSTEP` and `M:TFlex.Model.ExportToSTEP.Export(System.String)` for STEP recipes where applicable.
- `T:TFlex.Model.Model3D.ThickenExtrusion` and `F:TFlex.Model.Model3D.ThickenExtrusion.LengthValue.ValueNo` for exact one-sided extrusion.
- Existing verified session pattern from `.agents/skills/tflex-harness/SKILL.md`.

## C# Source

Snippet: `agent_workspace/recipes/helper_simple_extrusion.cs`

This recipe compiles with helper source set `all` from `src/tflex_harness/csharp_helpers`.

## Live Verification Report

Test: `helper_simple_extrusion`

Docs used:

- `D:\REALPROJECTS\tflex_api\llm\symbols.jsonl`
- DeepWiki `dwnmf/tflex_api` cross-checks for `ThickenExtrusion` and `ExportToSTEP` behavior.

Snippet: `agent_workspace/recipes/helper_simple_extrusion.cs`

Result: pass.

Evidence:

- live run directory: `artifacts/runs/20260525_120312_702012_recipe_helper_simple_extrusion`;
- helper source files were copied into the run directory and recorded with SHA256 hashes;
- stdout evidence: bboxSpanMm=20,20,8; GRB artifact helper_simple_extrusion.grb size 70812 bytes;
- run returned exit code `0` in the verified local T-FLEX CAD 17 environment.

Blockers: none on the verified local T-FLEX CAD 17 environment.

## Assumptions

- T-FLEX CAD 17 is installed locally and can initialize a 3D session.
- Helper source set `all` is available under `src/tflex_harness/csharp_helpers`.
- STEP export success is determined by a non-empty file artifact because `ExportToSTEP.Export` can return `False` while producing a valid non-empty STEP file in live evidence.

## Limitations

- This recipe validates helper-backed API paths and artifact evidence; it does not replace detailed visual CAD inspection.
- Output artifacts are written under the per-run `TFLEX_HARNESS_ARTIFACTS_DIR` through `EasySession.ArtifactPath`.
