---
name: tflex-harness
description: "Work on the local D:\\REALPROJECTS\\tflex_harness repository: T-FLEX CAD 17 harness/MCP code, C# snippet runner, recipes, live CAD validation, artifacts, diagnostics, and project documentation. Use this when editing, testing, debugging, or operating tflex-harness itself. Communicate in a concise caveman style while preserving exact commands, paths, and evidence."
---

# T-FLEX Harness

Use this skill for work inside `D:\REALPROJECTS\tflex_harness`: harness code, MCP server, C# snippet runner, recipes, live T-FLEX CAD checks, generated artifacts, diagnostics, and local project docs.

## Voice

User-facing style:

- Caveman concise. Short sentences. No fluff.
- Keep exact technical names: paths, commands, APIs, run dirs, errors.
- Do not hide uncertainty. Say “Not verified”, “Need live T-FLEX”, or “Not know yet”.
- Report evidence, not vibes.

## Repo Map

- Repo root: `D:\REALPROJECTS\tflex_harness`
- Package: `src/tflex_harness`
- Tests: `tests/unit`, `tests/smoke`, `tests/integration`
- Local skills: `.agents/skills`
- Generated run dirs: `artifacts/runs`
- Generated T-FLEX files: `artifacts/tflex_docs`
- Snippet candidates: `agent_workspace/snippets`
- C# helper sources: `src/tflex_harness/csharp_helpers`
- Event log: `logs/events.jsonl`
- Architecture/status: `goal.md`
- Local T-FLEX API docs: `D:\REALPROJECTS\tflex_api\llm`


## Current Focus: Targeted Fixes 1-3

As of 2026-05-25, `goal.md` has been reset to a compact plan. Ignore older phase sprawl unless needed for evidence lookup. Current work is only:

1. **Tables/specifications**
   - Generic `RichText` table-cell mutation works for `Таблицы/*`.
   - Live matrix: `artifacts/prototype_validation/20260525_220550_733488/prototype_table_cell_matrix.json`.
   - Result: `Таблицы` selected `7`, passed `7`, persisted `7`.
   - Same raw path is weak for `Спецификации/*`.
   - Live matrix: `artifacts/prototype_validation/20260525_220918_092578/prototype_table_cell_matrix.json`.
   - Result: `Спецификации` selected `20`, passed `1`, failed `19`, persisted `1`.
   - Next: find specification-specific API; do not keep retrying raw `RichText.GetTableByIndex(0)` as the main fix.

2. **Electrical documents**
   - Generic visible text replacement works only where `LineText` or non-table `RichText` is API-visible.
   - Direct proof: `artifacts/runs/20260525_220841_828547_recipe_prototype_replace_first_visible_text`, `firstVisibleText.persisted=True`.
   - Batch matrix: `artifacts/prototype_validation/20260525_220808_834096/prototype_first_visible_text_matrix.json`.
   - Result: `Электротехника` selected `8`, passed `4`, failed `4`, persisted `4`.
   - Next: probe failing electrical prototypes for variables, symbol-like objects, connector metadata, or electrical-specific API.

3. **Fragments/assemblies**
   - Semantic Fragment3D LCS insertion is live-proven.
   - Recipe: `helper_fragment_lcs_assembly`.
   - Live run: `artifacts/runs/20260525_220748_356485_recipe_helper_fragment_lcs_assembly`.
   - Evidence: `fragment.sourceLcs=FRAG_LCS`, `fragment.targetLcsNull=False`, `assembly.operationsAfter=1`, `assembly.saved=True`, `fragmentAssembly.persisted=True`.
   - Next: wire this path into document factory payloads.

Do not mark any of these complete without a fresh narrow live run for the exact changed path.

## Hard Rules

1. Run `git status --short` before tracked edits.
2. Do not commit generated artifacts unless user explicitly asks.
3. Do not touch unrelated untracked files. Known old untracked path may exist: `agent_workspace/snippets/crank_yoke_assembly/`.
4. Use exact search first: `rg`, `fff`, local docs grep.
5. For T-FLEX API behavior, also use `deepwiki-tflex-api`.
6. Prefer smallest validation:
   - Harness code: targeted unit/smoke test.
   - T-FLEX API shape: `compile_only` first.
   - T-FLEX behavior: live run only when needed.
7. For live snippets, capture run dir and stdout evidence.
8. If a live snippet prints success but times out, inspect `result.json`, `stdout.txt`, saved `.grb`, and stale `Snippet` process before judging failure.
9. Do not claim native T-FLEX behavior works without a live run proving the exact path.

## Common Commands

```powershell
python -m pytest tests/unit -v
python -m pytest tests/smoke -v
python -m tflex_harness.cli env
python -m tflex_harness.cli search "TFlex.Model.Document" --limit 5
python -m tflex_harness.cli recipes
python -m tflex_harness.cli state
python -m tflex_harness.cli run-csharp --mode compile_only --code "public class Program { public static int Main(){ return 0; } }"
python -m tflex_harness.cli document-factory-batch --payload-dir payloads --dry-run
python -m tflex_harness.cli document-factory-batch --failed-matrix artifacts/my_batch/document_factory_batch_matrix.json
python -m tflex_harness.cli document-factory-batch --payload-dir payloads --audit-open-only
tflex-harness-mcp
```

## Direct C# Runner Pattern

Use explicit references:

- `TFlexAPI` for application/session/document/2D API.
- `TFlexAPI3D` for 3D operations, geometry, fragments, mates.
- `TFlexCommandAPI` for command/UI API only.
- `TFlexAPIData` for data API only.

```powershell
$env:PYTHONPATH = Join-Path (Get-Location) 'src'
python -c "from tflex_harness.runner import run_csharp_snippet; result = run_csharp_snippet(code='public class Program { public static int Main(){ return 0; } }', mode='run', timeout_sec=30, references=[], artifact_prefix='manual_probe'); print(result)"
```

For snippet-generated outputs, write under `TFLEX_HARNESS_ARTIFACTS_DIR` / `EasySession.ArtifactPath(...)`. Do not write `.grb`/STEP files into random repo or user folders.

## C# Helper Source Policy

Use helper `.cs` files when they prevent repeated T-FLEX API mistakes. They are source files compiled with the visible snippet, not a hidden wrapper DLL.

Known helper sets:

- `easy_core`: `TFlexEasyUnits.cs`, `TFlexEasyDiagnostics.cs`
- `easy_session`: core plus `TFlexEasySession.cs`
- `easy_3d`: session/profile/gear/solid/placement helpers
- `easy_gears`: `TFlexEasyGears.cs` plus minimal dependencies
- `easy_export`: session/export helpers
- `easy_prototype`: installed `.grb` prototype copy/open/save helpers
- `easy_variables`: prototype/session helpers plus text/real variable mutation helpers
- `easy_text`: prototype/session helpers plus `RichText` table cell, visible 2D text replacement helpers, and first visible non-table text helpers
- `easy_document_properties`: prototype/session helpers plus writable `Document.Properties` string mutation helpers
- `all`: every helper source

For gear assemblies:

1. Prefer `TFlexEasyGears.cs` direct-XY profile helpers:
   - `EasyGears.ExternalTrapezoidGearAt(...)`
   - `EasyGears.ExternalTrapezoidGearWithBoreAt(...)`
   - `EasyGears.InternalTrapezoidGearRingAt(...)`
   - `EasyGears.CircleAt(...)`
2. Do not build centered gear profiles and then rely on body `MoveMm` unless the task specifically needs transformed bodies.
3. Use explicit tooth phase helpers:
   - `EasyGears.PhaseForGapAtAxisDeg(teeth, axisDeg)`
   - `EasyGears.PhaseForToothAtAxisDeg(teeth, axisDeg)`
   - `EasyGears.PlanetToothFacingSunPhaseDeg(planetAxisDeg)`
4. For simplified trapezoid gear visuals, start with `EasyGearToothStyle.Clearanced`; use `Wide` only if the user wants chunky schematic teeth.
5. Print mesh evidence with radial clearances and planet center radii. BBox alone is not enough for gear mesh quality.

## Validation Ladder

### Harness code

1. Run the narrowest relevant unit test.
2. Run related smoke test.
3. Run integration only if live T-FLEX is required and scope allows.

### T-FLEX API snippets

1. Search `D:\REALPROJECTS\tflex_api\llm\symbols.jsonl`.
2. Open matching `D:\REALPROJECTS\tflex_api\llm\types\*.md`.
3. Ask DeepWiki repo `dwnmf/tflex_api` for exact class/member behavior.
4. Compile with `mode='compile_only'`.
5. Run live if compile passes and behavior matters.
6. Save evidence under `artifacts/runs/...` and `.grb` outputs under `artifacts/tflex_docs/...`.

## Live Session Pattern

Known-good setup for writeable 3D live runs:

```csharp
var setup = new ApplicationSessionSetup();
setup.ReadOnly = false;
setup.Enable3D = true;
setup.EnableDOCs = false;
setup.EnableMacros = false;
setup.PromptToSaveModifiedDocuments = false;
setup.ProtectionLicense = ApplicationSessionSetup.License.TFlex3D;
bool init = Application.InitSession(setup);
```

Close documents and exit session in `finally`:

```csharp
try { if (document != null) document.Close(); } catch {}
if (Application.IsSessionInitialized) Application.ExitSession();
```

## Verified Export API Facts

Verified locally in T-FLEX CAD 17 on 2026-05-25.

- `EasyExport.Grb(doc, path)` wraps `Document.SaveAs(path)`.
- `EasyExport.Step(doc, path)` wraps `Document.ExportToSTEP.Export(path)`.
- `EasyExport.Dxf(doc, path)` wraps `Document.ExportToDXF.Export(path)`.
- `EasyExport.Dwg(doc, path)` wraps `Document.ExportToDWG.Export(path)`.
- `ExportToSTEP.Export(...)` can return `False` while still writing a valid non-empty STEP. Treat non-empty file artifact as success unless newer live evidence contradicts this.
- 2D PDF uses `new TFlex.Model.ExportToPDF(document)`, not `Document.ExportToPDF`; `Document.ExportToPDF` does not compile in T-FLEX CAD 17.
- For headless PDF export, set `OpenExportFile=false` and `IsSelectPagesDialogEnabled=false`.
- Live PDF export failed with `Error loading module PDFExport.dll` until `PDFExport.dll` was copied from `C:\Program Files\T-FLEX CAD 17\Program` to the snippet current directory. `EasyExport.Pdf(...)` now performs this copy by searching `PATH`.
- Live DXF/DWG drawing export succeeded with `easy.dxfExportResult=True`, `easy.dxfSaved=True`, `easy.dwgExportResult=True`, and `easy.dwgSaved=True`. DXF header evidence: `SECTION`, `$ACADVER`, `AC1027`; DWG header bytes: `41 43 31 30 32 37` (`AC1027`).

## Verified 3D API Facts

Verified locally in T-FLEX CAD 17 on 2026-05-22.

### Variables and expressions

- Create `Variable` objects in their own `doc.BeginChanges(...)` / `doc.EndChanges()` block before geometry that references them.
- Mixing variable creation and dependent 3D operations in one changes block can yield `CompleteError` and disposed-object errors.
- T-FLEX variable trigonometry uses degrees for `sin(Angle)` and `cos(Angle)`. Do not convert `Angle` to radians unless new live evidence says otherwise.

### Primitive solids

- For simple parametric solids, prefer `TFlex.Model.Model3D.Block` and `TFlex.Model.Model3D.Cylinder`.
- `Cylinder` uses `Diameter` and `Height`, not `Radius`.
- `Cylinder.Geometry.Axis` can be non-null after successful `EndChanges()`.
- `Cylinder.Geometry.Surface` was null in simple primitive probes. Do not assume it exists for tangency mates.
- `Block.Geometry.Plane` can be non-null after successful `EndChanges()`.

### Transformations

Use `Object3D.Transformations.AddBaseTransfGroup()` with:

- `TransformationGroup.AddMoveTransf(TransformationCoordinate.X/Y/Z, Parameter)`
- `TransformationGroup.AddRotateTransf(TransformationCoordinate.X/Y/Z, Parameter)`

Do not use `Object3D.VolatileTransformations` in new snippets. Live T-FLEX CAD 17 can throw: `Property VolatileTransformation is obsolete. Use Transformations property instead`.

For flat gear profiles, prefer direct XY profile coordinates from `TFlexEasyGears.cs` over body transforms. Live evidence on 2026-05-25 showed direct-XY planetary gears reopened from `.grb` with three planets still at R42; transformed-centered gear bodies were visually confusing in CAD inspection.

## Verified Fragment3D + LCS Path

Use this as the reliable assembly placement path.

1. Create source part `.grb`.
2. In the part, create a named `PointsLCS`:
   - `new PointsLCS(document)`
   - `lcs.Name = "FRAG_LCS"`
   - `lcs.UseForFragment = true`
   - `lcs.UseForFragmentFixing = true`
   - build it from three `CoordinateNode3D` objects via `Geometry.Point`:
     - `PointToOrigin`
     - `PointToAxisX`
     - `PointToAxisY`
3. Save and close the part document.
4. Create assembly document.
5. Create target `PointsLCS` in assembly.
6. Insert fragment:
   - `Fragment3D fragment = new Fragment3D(partFile, asmDocument);`
   - `fragment.FixByFragmentLCS("FRAG_LCS", targetLCS);`
7. `EndChanges()` and save assembly.

Runtime facts:

- `Fragment3D.FileName` compiles with obsolete warning; prefer `Fragment3D.FilePath`.
- `Fragment3D.SourceLCSName` and `Fragment3D.TargetLCS` expose the placement relation.
- Live run `artifacts/runs/20260522_200532_825406_probe_fragment_lcs_fix` returned:
  - `partEnd=OK`
  - `asmEnd=OK`
  - `fragmentSourceLCSAfter=FRAG_LCS`
  - `fragmentTargetLCSNullAfter=False`
  - `asmAfter=1`
- Saved `.grb` files under `artifacts/tflex_docs/20260522_200532_574925_probe_fragment_lcs_fix`.
- Newer recipe proof `artifacts/runs/20260525_220748_356485_recipe_helper_fragment_lcs_assembly` returned `fragmentAssembly.persisted=True`, `assembly.operationsAfter=1`, `part.outputSize=11444`, and `assembly.outputSize=9935`.

## Native Mate Status

Treat native `Mate` creation as unverified unless a newer live probe proves the exact geometry pair.

### Confirmed API shape

- `Document3D.GetMates(document)` exists.
- `new Mate(document)` exists.
- Runtime reflection showed:
  - `Mate.Operation1` and `Mate.Operation2` are read-only.
  - `Mate.Element1`, `Mate.Element2`, and `Mate.Type` are writable.
  - `Mate.Element1/Element2` property type is `TFlex.Model.Model3D.Geometry.Geometry`.
- `Mate.MateType` values include:
  - `Coincidence`
  - `Parallelism`
  - `Perpendicularity`
  - `Tangency`
  - `Concentricity`
  - `Distance`
  - `Angle`
  - `AngAngTransmission`
  - `AngLinTransmission`
  - `LinLinTransmission`
- Reflection run: `artifacts/runs/20260522_200859_604615_probe_mate_fragment_reflection`.

### Failed primitive mate probes

All returned `CompleteError` and `Document3D.GetMates(doc).Count == 0`:

- `Mate.Type = Mate.MateType.Concentricity` plus `Mate.Element1 = c1.Geometry.Axis`, `Mate.Element2 = c2.Geometry.Axis`.
- `Mate.SetGeomReference(k, new Object3D.GeomReference(axisOrPlane))` for adjacent key pairs `0,1` through `6,7`, both axis/concentricity and plane/distance cases.
- Runs:
  - `artifacts/runs/20260522_195730_527663_probe_mate_reference_ids`
  - `artifacts/runs/20260522_195807_669951_probe_mate_setgeom_matrix`

### Failed Fragment3D mate probes

All returned `CompleteError` and `Document3D.GetMates(doc).Count == 0` when actual mate geometry was non-null:

- `Mate.Element1/Element2 = fragment.Geometry.Axis`
- `Mate.Element1/Element2 = fragment.Geometry.Plane`
- `Mate.Element1/Element2 = fragment.TargetLCS.Geometry.AxisZ`
- Both `Fixing=ByFragmentLCS` and `Fixing=NoFixing` cases failed.
- `Mate.SetGeomReference(k, new Object3D.GeomReference(fragment.Geometry.Axis))` for key pairs `0,1` through `8,9` failed.
- Runs:
  - `artifacts/runs/20260522_201144_983401_probe_fragment_native_mates`
  - `artifacts/runs/20260522_201224_942060_probe_fragment_native_mates_nofix`
  - `artifacts/runs/20260522_201300_458192_probe_fragment_mate_setgeom`

## Fragment Freedom and Selection Findings

### Freedom properties

- Runtime reflection shows these are writable:
  - `Fragment3D.MoveX/MoveY/MoveZ`
  - `Fragment3D.RotateX/RotateY/RotateZ`
  - `Fragment3D.FreedomPropertyContainer.EnableMovementX/Y/Z`
  - `Fragment3D.FreedomPropertyContainer.EnableRotationX/Y/Z`
- Live probes showed setters did not persist on inserted fragments; values read back as `False`.
- Setting `PointsLCS.MoveX/MoveY/MoveZ/RotateX/RotateY/RotateZ = true` in the source part saved correctly, but inserted `Fragment3D` still read all movement/rotation flags as `False`.
- Native `Mate` still returned `CompleteError`.
- Runs:
  - `artifacts/runs/20260522_201615_218992_probe_freedom_reflection`
  - `artifacts/runs/20260522_201652_796028_probe_fragment_mate_freedoms`
  - `artifacts/runs/20260522_201800_399319_probe_lcs_source_freedoms`

### Selection and subfragments

- `SelectionContainerExtensions.SelectSubFragment` selects subfragments by `FragmentIdChain`, not internal cylinder/LCS geometry.
- Reflection showed overloads:
  - `SelectSubFragment(SelectionContainer, Fragment3D, FragmentIdChain)`
  - `SelectSubFragment(SelectionContainer, Fragment3D, IEnumerable<ObjectId>)`
  - `SelectObject(SelectionContainer, ObjectIdChain)`
  - `GetObjectIdChains(ModelObject)`
  - `GetObjectIdChains(SelectionContainer)`
- For a first-level `Fragment3D`, `GetObjectIdChains(fragment)` returned only the fragment `ObjectId`.
- `SelectSubFragment(selection, fragment, new[] { fragment.ObjectId })` selected the same top-level fragment.
- Runs:
  - `artifacts/runs/20260522_202057_184069_probe_selection_reflection`
  - `artifacts/runs/20260522_202224_565086_probe_objectidchain_reflection`
  - `artifacts/runs/20260522_202302_194444_probe_selection_chains`

### Fragment geometry collections

- `fragment.Geometry.Points` and `fragment.Geometry.Planes` enumerated three null elements for the cylinder fragment probe.
- Do not use those collections as reliable target-LCS construction points without another live proof.
- Run: `artifacts/runs/20260522_202538_400207_probe_fragment_geometry_points_safe`.

## Web and Forum Evidence

Use these as context, not runtime proof:

- T-FLEX help: assembly mates need selected elements and one fixed component: `https://www.tflexcad.ru/help/cad/17/mate.htm`
- T-FLEX help: LCS-based fragment insertion supports “mating element” and “allowed degrees of freedom”: `https://www.tflexcad.ru/help/cad/17/assemblylcs.htm`
- T-FLEX forum thread about API mate/geometric references: `https://www.tflex.ru/forum/index.php?FID=14&MID=44630&PAGE_NAME=read&TID=6443`
- DeepWiki can hallucinate details. Example: it described `Fragment3D.MoveX` as numeric translation, but runtime reflection proved it is `System.Boolean`.

## Current Native Mate Hypotheses

Most likely next routes:

1. Find exact Open API command name for the UI mate command and test `Application.RunSystemCommand(...)`.
   - Docs say command names appear in tooltips if T-FLEX option “Включить в подсказки имена команд в Open API” is enabled.
   - `Application.RunSystemCommand(System.String, ModelObject[], SystemCommandFinishedCallback)` exists.
2. Find API for the LCS “mating element” mentioned in T-FLEX help.
3. Create target LCS directly from supported component geometry, not standalone coordinate nodes.
4. Investigate whether UI-created mate `.grb` can be introspected to reveal valid `Mate.Element1/Element2` owner/reference structure.

Do not retry already-failed direct `Mate.Element1/Element2 = fragment.Geometry.Axis/Plane` unless the setup materially changes.

## Reporting Template

Use this shape:

```text
Done. Me checked.

Changed:
- `path`

Verified:
- `command or run dir`

Not verified:
- Exact gap.
```

Rules:

- Separate `Changed`, `Verified`, and `Not verified` when edits or partial validation exist.
- Include run dirs for live T-FLEX evidence.
- Mention if generated artifacts were intentionally not committed.
- Mention if commit/push happened and include commit hash.
