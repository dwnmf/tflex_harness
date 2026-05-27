---
name: tflex-harness
description: Operate T-FLEX CAD 17 through the local tflex-harness CLI/MCP: docs search, visible C# snippets, checked-in C# helpers, recipes, live validation, and artifact evidence.
---

# tflex-harness

Use this skill when working with T-FLEX CAD 17 through `tflex-harness`: API docs search, C# snippet compile/run, verified recipes, prototype documents, document factory, assembly validation, and MCP tools.

For first-time install or reconnect, read `install.md` first.

## Installed command shape

Use the global commands. No `cd` needed if installed editable from the repo:

```powershell
tflex-harness env
tflex-harness search "TFlex.Model.Document" --limit 5
tflex-harness recipes
tflex-harness run-csharp --mode compile_only --code "public class Program { public static int Main(){ return 0; } }"
tflex-harness-mcp
```

If commands cannot find checked-in recipes/helpers, set:

```powershell
$env:TFLEX_HARNESS_REPO_DIR = "<repo>"
```

API docs are not bundled. Use the docs repo:

```powershell
git clone https://github.com/dwnmf/tflex_api <tflex-api-docs>
$env:TFLEX_API_DOCS_DIR = "<tflex-api-docs>"
```

If `TFLEX_API_DOCS_DIR` is not set, the harness tries a sibling checkout named `tflex_api` next to `<repo>`.

## Normal workflow

1. Search exact symbols first:

```powershell
tflex-harness search "Document3D.GetMates" --limit 10
```

2. Compile small C# probes before live runs:

```powershell
tflex-harness run-csharp --mode compile_only --reference TFlexAPI --reference TFlexAPI3D --code "public class Program { public static int Main(){ return 0; } }"
```

3. Run live T-FLEX only for behavior that compile/docs cannot prove.
4. Save evidence: run dir, stdout keys, generated `.grb`/STEP artifacts.
5. Promote repeated working snippets to `agent_workspace/recipes` only with docs and live evidence.

## C# helper policy

Helpers are visible `.cs` source compiled with the snippet, not hidden wrapper DLLs.

Helper files live under `src/tflex_harness/csharp_helpers/`:

- `TFlexEasyUnits.cs` — unit conversion helpers.
- `TFlexEasyDiagnostics.cs` — key/value evidence, bbox evidence, simple assertions.
- `TFlexEasySession.cs` — T-FLEX session start/stop and artifact paths.
- `TFlexEasyPrototype.cs` — open/copy installed prototype documents.
- `TFlexEasyProfiles.cs` — basic 2D profiles.
- `TFlexEasySketchProfiles.cs` — higher-level sketch/profile shapes.
- `TFlexEasySolids.cs` — blocks, cylinders, extrusions, cutters.
- `TFlexEasyPlacement.cs` — object transformations and placement.
- `TFlexEasyWorkplanes.cs` — standard workplanes and axis mapping.
- `TFlexEasyBoolean.cs` — boolean add/subtract/intersect helpers.
- `TFlexEasyFeatures.cs` — reusable part feature builders.
- `TFlexEasyEvidence.cs` — manifest and validation evidence helpers.
- `TFlexEasyExport.cs` — GRB/STEP/PDF/DXF/DWG export helpers.
- `TFlexEasyReopen.cs` — save/close/reopen verification helpers.
- `TFlexEasyVariables.cs` — document variable helpers.
- `TFlexEasyText.cs` — text/table text helpers.
- `TFlexEasyDocumentProperties.cs` — document property helpers.
- `TFlexEasySpecifications.cs` — BOM/specification helpers.
- `TFlexEasyAssemblyBuild.cs` — fragment part creation, target LCS, fragment insertion.
- `TFlexEasyAssemblyValidation.cs` — collision/contact, fragment DOF-lite, mate graph validation.
- `TFlexEasyMateInspector.cs` — existing native mate graph/owner dump.
- `TFlexEasyNativeMates.cs` — create native mates from real body topology, e.g. edge-axis concentricity.
- `TFlexEasyCommandProbe.cs` — command list and `RunSystemCommand` probing.

Known helper sets:

- `easy_core`
- `easy_session`
- `easy_3d`
- `easy_gears`
- `easy_export`
- `easy_prototype`
- `easy_variables`
- `easy_text`
- `easy_specification`
- `easy_document_properties`
- `easy_assembly_validation`
- `easy_assembly_build`
- `easy_mate_inspection`
- `easy_native_mates`
- `easy_all_live`
- `all`

Example:

```powershell
tflex-harness run-csharp --mode compile_only --helper easy_assembly_validation --code "using TFlexEasy; public class Program { public static int Main(){ return 0; } }"
```

## Assembly validation status

Live-proven helper: `src/tflex_harness/csharp_helpers/TFlexEasyAssemblyValidation.cs`.

Latest verified recipe run:

```text
artifacts/runs/20260526_233717_009768_recipe_helper_assembly_validation
```

What it proves:

- exact body collision via AABB broad phase + `BaseBody.Clash(...)`;
- face contact is not false collision;
- floating `Fragment3D` detection;
- DOF-lite and estimated constraint counting;
- native mate enumeration hook through `Document3D.GetMates(doc)`.

Key evidence:

```text
bad.summary.collisionCount=1
bad.summary.floatingFragmentCount=1
bad.fragment.1.estimatedRemainingDof=6
good.summary.fullyConstrainedFragmentCount=2
good.summary.estimatedDofRemaining=0
touch.summary.collisionCount=0
touch.summary.contactCount=1
touch.summary.estimatedDofRemaining=0
assemblyValidation.live=True
```

Native mate creation is live-proven through body topology:

- use `TFlexEasyNativeMates.cs`;
- take `ModelEdge.Geometry.Axis` or `ModelFace.Geometry.Surface/Plane`;
- do not use `fragment.Geometry.Axis/Plane` directly.

Evidence:

```text
artifacts/runs/20260527_144832_474157_fragment_native_mate_positive_probe
asm.mate.end=OK
asm.mateCount=1
asm.mate.0.op1=fixed_fragment
asm.mate.0.op2=mated_fragment

artifacts/runs/20260527_144900_168574_reopen_fragment_native_mate_positive
reopen.mateCount=1
```

## Safety rules

- Do not write `.grb`, STEP, logs, or generated files outside harness artifact directories unless the user explicitly asks.
- Do not run broad prototype/document batches unless the user asks; prefer small live probes.
- Do not claim T-FLEX runtime behavior works without a live run proving that exact path.
- Do not commit generated artifacts.
- Keep C# snippets visible and evidence-driven.

## Useful commands

```powershell
tflex-harness env
tflex-harness recipes
tflex-harness state
tflex-harness prototypes-scan
tflex-harness prototypes-list --category Чертежи
tflex-harness run-recipe helper_assembly_validation --timeout-sec 120
```

MCP server:

```powershell
tflex-harness-mcp
```
