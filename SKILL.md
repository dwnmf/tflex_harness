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

Limit: positive native `MateEdgeCount>0` still needs a real native-mate `.grb` or a working mate creation recipe.

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
