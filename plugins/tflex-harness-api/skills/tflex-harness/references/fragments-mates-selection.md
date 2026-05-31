# Fragments, Mates, Freedom, Selection

## Contents
- Reliable Fragment3D + LCS path
- Native Mate status
- Fragment freedom findings
- Selection and geometry collection findings
- Web/forum context
- Current hypotheses

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
