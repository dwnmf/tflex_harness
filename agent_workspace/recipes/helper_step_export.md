# Recipe: helper_step_export

## Purpose

Create a simple helper-backed 3D body and export STEP artifact evidence.

## Documentation Evidence

Docs used:

- `D:\REALPROJECTS\tflex_api\llm\symbols.jsonl`
- `P:TFlex.Model.Document.ExportToSTEP` and `M:TFlex.Model.ExportToSTEP.Export(System.String)` for STEP recipes where applicable.
- `T:TFlex.Model.Model3D.ThickenExtrusion` and `F:TFlex.Model.Model3D.ThickenExtrusion.LengthValue.ValueNo` for exact one-sided extrusion.
- Existing verified session pattern from `.agents/skills/tflex-harness/SKILL.md`.

## C# Source

Snippet: `agent_workspace/recipes/helper_step_export.cs`

This recipe compiles with helper source set `all` from `src/tflex_harness/csharp_helpers`.

## Live Verification Report

Test: `helper_step_export`

Docs used:

- `D:\REALPROJECTS\tflex_api\llm\symbols.jsonl`
- DeepWiki `dwnmf/tflex_api` cross-checks for `ThickenExtrusion` and `ExportToSTEP` behavior.

Snippet: `agent_workspace/recipes/helper_step_export.cs`

Result: pass.

Evidence:

- live run directory: `artifacts/runs/20260525_120314_679135_recipe_helper_step_export`;
- helper source files were copied into the run directory and recorded with SHA256 hashes;
- stdout evidence: STEP artifact helper_simple.step size 154986 bytes;
- run returned exit code `0` in the verified local T-FLEX CAD 17 environment.

Blockers: none on the verified local T-FLEX CAD 17 environment.

## Assumptions

- T-FLEX CAD 17 is installed locally and can initialize a 3D session.
- Helper source set `all` is available under `src/tflex_harness/csharp_helpers`.
- STEP export success is determined by a non-empty file artifact because `ExportToSTEP.Export` can return `False` while producing a valid non-empty STEP file in live evidence.

## Limitations

- This recipe validates helper-backed API paths and artifact evidence; it does not replace detailed visual CAD inspection.
- Output artifacts are written under the per-run `TFLEX_HARNESS_ARTIFACTS_DIR` through `EasySession.ArtifactPath`.
