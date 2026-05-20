# Recipe: create_simple_3d_extrusion

## Purpose

Create a hidden 3D T-FLEX document, build a circular 2D area profile on a standard workplane, create a `ThickenExtrusion`, verify that a 3D operation/body/geometry exists, save the document as `.grb`, close it, and exit the API session.

## Documentation Evidence

Local documentation source: `D:\REALPROJECTS\tflex_api`.

- `M:TFlex.Application.InitSession(TFlex.ApplicationSessionSetup)` — initialize Open API from an external EXE.
- `F:TFlex.ApplicationSessionSetup.License.TFlex3D` — request a 3D-capable T-FLEX license.
- `P:TFlex.ApplicationSessionSetup.Enable3D` — enable 3D module loading for the session.
- `M:TFlex.Application.NewDocument(System.Boolean,System.Boolean)` — create a new document; this recipe uses `b3D=true`, `visible=false`.
- `M:TFlex.Model.Document.BeginChanges(System.String)` and `M:TFlex.Model.Document.EndChanges` — wrap document mutations and apply them.
- `M:TFlex.Model.Model2D.FreeNode.#ctor(TFlex.Model.Document,TFlex.Model.Parameter,TFlex.Model.Parameter)` — create the circular profile center.
- `M:TFlex.Model.Model2D.CircleConstruction.#ctor(TFlex.Model.Document)` and `SetCenterAndRadius` — create construction circle geometry.
- `M:TFlex.Model.Model2D.Area.AppendContour` and `T:TFlex.Model.Model2D.ConstructionContourSegment` — create a closed area contour from the circle.
- `M:TFlex.Model.Model3D.StandardWorkplane.#ctor(TFlex.Model.Document,TFlex.Model.Model3D.StandardWorkplane.StandardType)` — create a standard 3D workplane.
- `M:TFlex.Model.Model3D.AreaProfile.#ctor(TFlex.Model.Document)`, `P:TFlex.Model.Model3D.AreaProfile.Area`, `P:TFlex.Model.Model3D.AreaProfile.WorkSurface` — build a 3D profile from the 2D area.
- `T:TFlex.Model.Model3D.ThickenExtrusion` — official XML example shows `Thickness1`, `LengthType`, `ForwardLength`, and `Profile.Add(profile.Geometry.SheetContour)`.
- `M:TFlex.Model.Model3D.Document3D.GetOperations(TFlex.Model.Document)` — verify the 3D operation count increased.
- `P:TFlex.Model.Model3D.Operation.Body` and `P:TFlex.Model.Model3D.Operation.Geometry` — verify runtime 3D result objects are not null.
- `P:TFlex.Model.Model3D.Operation.GeometryData.AABoundBox` — get the axis-aligned operation bounding box.
- `P:TFlex.Model.Model3D.Geometry.ModelBox.Minimum`, `Maximum`, and `Valid` — verify the bounding box is valid and has positive X/Y/Z extents.
- `P:TFlex.Model.Model3D.Geometry.BasePoint3D.X`, `Y`, and `Z` — compute observable bounding-box sizes from model points.
- `M:TFlex.Model.Document.SaveAs(System.String)` and `M:TFlex.Model.Document.Close` — save and close the artifact document.
- `M:TFlex.Application.ExitSession` — paired session exit.

## C# Source

See `agent_workspace/recipes/create_simple_3d_extrusion.cs`.

The recipe intentionally follows the official `ThickenExtrusion` example from `llm/symbols.jsonl` rather than wrapping the operation behind a high-level CAD helper. This keeps the exact T-FLEX API sequence visible for LLM iteration.

## Verification

Live verification performed on 2026-05-20 against local T-FLEX CAD 17:

```text
init=True
docNull=False
operationsBefore=0
endChanges=OK
operationsAfter=1
operationType=TFlex.Model.Model3D.ThickenExtrusion
bodyNull=False
geometryNull=False
bboxValid=True
bboxMin=-0.05,-0.011,-0.009
bboxMax=0.01,0.009,0.011
bboxSize=0.06,0.02,0.02
bboxPositive=True
saved=True
exists=True
exited=False
```

Artifact evidence:

- saved `.grb`: `artifacts/tflex_docs/20260520_224300_659083_manual_3d_extrusion/manual_3d_extrusion.grb`
- run directory: `artifacts/runs/20260520_224300_887226_manual_3d_extrusion`
- bounding-box verification run: `artifacts/runs/20260520_225011_637244_manual_3d_bbox4`

## Assumptions

- T-FLEX CAD 17 is installed at `C:\Program Files\T-FLEX CAD 17`.
- The local environment can obtain `ApplicationSessionSetup.License.TFlex3D`.
- `PATH` includes `C:\Program Files\T-FLEX CAD 17\Program` at runtime so native dependencies load.
- Hidden 3D document creation is available via `Application.NewDocument(true, false)`.

## Limitations

- This recipe verifies the operation count, operation type, non-null body/geometry, a valid positive axis-aligned bounding box, and saved file evidence.
- It creates a minimal circular thicken extrusion only.
- It writes only to an artifact path created by the harness and does not touch user documents.
