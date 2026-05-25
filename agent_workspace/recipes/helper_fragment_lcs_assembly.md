# Recipe: helper_fragment_lcs_assembly

## Purpose

Create a source 3D part with a fragment LCS, create an assembly, insert the part as `Fragment3D`, fix it by source/target `PointsLCS`, save both `.grb` outputs, and verify placement evidence.

## Documentation Evidence

Docs used:

- Prior live probe `artifacts/runs/20260522_200532_825406_probe_fragment_lcs_fix`.
- Verified Fragment3D + LCS path recorded in `tflex-harness` skill.

## C# Source

Snippet: `agent_workspace/recipes/helper_fragment_lcs_assembly.cs`

## Live Verification Report

Test: `helper_fragment_lcs_assembly`

Docs used:

- Prior live probe `artifacts/runs/20260522_200532_825406_probe_fragment_lcs_fix`.

Snippet: `agent_workspace/recipes/helper_fragment_lcs_assembly.cs`

Result: pass.

Evidence:

- live run directory: `artifacts/runs/20260525_220748_356485_recipe_helper_fragment_lcs_assembly`;
- command: `python -m tflex_harness.cli run-recipe helper_fragment_lcs_assembly --timeout-sec 120`;
- stdout: `part.end=OK`;
- stdout: `part.operations=1`;
- stdout: `source.useForFragment=True`;
- stdout: `source.useForFragmentFixing=True`;
- stdout: `part.saved=True`;
- stdout: `part.outputSize=11444`;
- stdout: `fragment.sourceLcs=FRAG_LCS`;
- stdout: `fragment.targetLcsNull=False`;
- stdout: `assembly.end=OK`;
- stdout: `assembly.operationsBefore=0`;
- stdout: `assembly.operationsAfter=1`;
- stdout: `fragment.sourceLcsAfter=FRAG_LCS`;
- stdout: `fragment.targetLcsNullAfter=False`;
- stdout: `assembly.saved=True`;
- stdout: `assembly.outputSize=9935`;
- stdout: `fragmentAssembly.persisted=True`;
- run returned exit code `0`.

Blockers: none for the verified `Fragment3D.FixByFragmentLCS` path.

## Limitations

- Creates a minimal block fragment and assembly proof, not a full enterprise BOM assembly.
- Verifies LCS fixing path and saved GRB artifacts.
