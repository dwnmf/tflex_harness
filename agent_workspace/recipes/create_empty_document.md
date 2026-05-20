# Recipe: create_empty_document

Status: verified live on this machine.

## Purpose

Create an invisible empty 2D T-FLEX CAD document from an external C# EXE, save it to a temporary `.grb` file, close the document, and exit the Open API session.

## Documentation Evidence

From `D:\REALPROJECTS\tflex_api\llm\symbols.jsonl` and type page `llm/types/TFlexAPI__TFlex.Model.Document__8a0793a4.md`:

- `M:TFlex.Application.InitSession(TFlex.ApplicationSessionSetup)` — initialize Open API from an external EXE.
- `M:TFlex.Application.NewDocument(System.Boolean,System.Boolean)` — create a new document; `b3D=false` creates non-3D prototype, `visible=false` keeps it hidden.
- `M:TFlex.Model.Document.SaveAs(System.String)` — save document to another file, returns `true` on success.
- `P:TFlex.Model.Document.FileName` — resulting file name.
- `P:TFlex.Model.Document.Title` — document title.
- `M:TFlex.Model.Document.Close` — close the document; no operations are valid on it afterwards.
- `M:TFlex.Application.ExitSession` — paired session exit.

## C# Source

See `agent_workspace/recipes/create_empty_document.cs`.

The recipe expects environment variable:

```text
TFLEX_RECIPE_OUTPUT_FILE=<absolute path to .grb>
```

## Verification

Test:

```powershell
python -m pytest tests/integration/test_tflex_live_document.py -v
```

Observed evidence from the live run:

```text
init=True
docNull=False
title=Default 1
saved=True
exists=True
fileName=<artifact .grb path>
session=False
```

The test additionally verifies that the saved `.grb` file exists under `artifacts/tflex_docs/` and has non-zero size.

## Assumptions

- T-FLEX CAD 17 is installed at `C:\Program Files\T-FLEX CAD 17`.
- The external process can obtain the `TFlexAPI` license.
- `PATH` includes `C:\Program Files\T-FLEX CAD 17\Program` at runtime so native dependencies load.

## Limitations

- This creates and saves an empty 2D document only.
- It does not modify geometry or validate object counts.
- It writes only to an artifact path created by the harness and does not touch user documents.
