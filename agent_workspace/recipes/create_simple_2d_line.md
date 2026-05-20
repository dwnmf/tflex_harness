# Recipe: create_simple_2d_line

Status: verified live on this machine.

## Purpose

Create an invisible 2D T-FLEX CAD document, add two free 2D nodes and a line construction through those nodes, save the document as `.grb`, close it, and exit the Open API session.

## Documentation Evidence

From `D:\REALPROJECTS\tflex_api\llm\symbols.jsonl` and type pages:

- `M:TFlex.Application.InitSession(TFlex.ApplicationSessionSetup)` — initialize Open API from an external EXE.
- `M:TFlex.Application.NewDocument(System.Boolean,System.Boolean)` — create a new document; `b3D=false`, `visible=false`.
- `M:TFlex.Model.Document.BeginChanges(System.String)` — open a document change block before modifications.
- `M:TFlex.Model.Document.EndChanges` — apply changes and close the change block; returns `OK` for valid changes.
- `M:TFlex.Model.Model2D.FreeNode.#ctor(TFlex.Model.Document,TFlex.Model.Parameter,TFlex.Model.Parameter)` — create a free 2D node at model coordinates.
- `M:TFlex.Model.Model2D.LineConstruction.#ctor(TFlex.Model.Document)` — create a construction line object in the document.
- `M:TFlex.Model.Model2D.LineConstruction.SetThroughNodes(TFlex.Model.Model2D.Node,TFlex.Model.Model2D.Node)` — make a line through two nodes.
- `P:TFlex.Model.Model2D.LineConstruction.LineType` — verifies the constructed line mode; observed `ThroughNodes`.
- `M:TFlex.Model.Document.Get2DObjects` — enumerate created 2D objects; observed two `FreeNode` objects and one `LineConstruction`.
- `M:TFlex.Model.Document.SaveAs(System.String)` — save document to another file.
- `M:TFlex.Model.Document.Close` — close the document.
- `M:TFlex.Application.ExitSession` — paired session exit.

The `LineConstruction` type docs also include the same official example pattern:

```csharp
Document document = TFlex.Application.ActiveDocument;
document.BeginChanges("Прямая");
FreeNode fn1 = new FreeNode(document, 10, 10);
FreeNode fn2 = new FreeNode(document, 50, 10);
LineConstruction lc = new LineConstruction(document);
lc.SetThroughNodes(fn1, fn2);
document.EndChanges();
```

## C# Source

See `agent_workspace/recipes/create_simple_2d_line.cs`.

The recipe expects environment variable:

```text
TFLEX_RECIPE_OUTPUT_FILE=<absolute path to .grb>
```

## Verification

Test:

```powershell
python -m pytest tests/integration/test_tflex_live_geometry.py -v
```

Observed live evidence:

```text
init=True
docNull=False
endChanges=OK
n1=10,10
n2=50,10
lineType=ThroughNodes
object2dType=TFlex.Model.Model2D.FreeNode
object2dType=TFlex.Model.Model2D.FreeNode
object2dType=TFlex.Model.Model2D.LineConstruction
objects2d=3
saved=True
exists=True
session=False
```

The test additionally verifies that the saved `.grb` file exists under `artifacts/tflex_docs/` and has non-zero size.

## Live Verification Report

Test: `create_simple_2d_line`

Docs used:

- `D:\REALPROJECTS\tflex_api\llm\symbols.jsonl`
- `D:\REALPROJECTS\tflex_api\llm\types\TFlexAPI__TFlex.Model.Document__8a0793a4.md`
- T-FLEX 2D type pages for `FreeNode` and `LineConstruction`.

Snippet: `agent_workspace/recipes/create_simple_2d_line.cs`

Result: pass.

Evidence:

- stdout contains `endChanges=OK`, `lineType=ThroughNodes`, `objects2d=3`, `saved=True`, and `exists=True`;
- observed object types include two `FreeNode` objects and one `LineConstruction`;
- saved `.grb` artifact exists and is non-empty;
- live tests `tests/integration/test_tflex_live_geometry.py` and `tests/integration/test_tflex_recipes.py::test_run_create_simple_2d_line_recipe_live` pass.

Blockers: none on the verified local T-FLEX CAD 17 environment.

## Assumptions

- T-FLEX CAD 17 is installed at `C:\Program Files\T-FLEX CAD 17`.
- The external process can obtain the `TFlexAPI` license.
- `PATH` includes `C:\Program Files\T-FLEX CAD 17\Program` at runtime so native dependencies load.

## Limitations

- This recipe creates a construction line, not a visible outline/segment drawing line.
- It verifies object construction through returned properties and saved file evidence, not by screenshot.
- It writes only to an artifact path created by the harness and does not touch user documents.
