# Recipe: save_document_as_temp

## Purpose

Create a hidden temporary 2D T-FLEX document, save it to a caller-provided or harness-generated `.grb` artifact path, write a small marker into `TFLEX_HARNESS_ARTIFACTS_DIR`, close the document, and exit the API session.

This recipe exists as the narrow save-path smoke from `goal.md` milestone 6. It intentionally does not modify user documents or save an existing active document.

## Documentation Evidence

Local documentation source: `D:\REALPROJECTS\tflex_api`.

- `M:TFlex.Application.InitSession(TFlex.ApplicationSessionSetup)` — initialize Open API from an external EXE.
- `P:TFlex.ApplicationSessionSetup.ReadOnly` — recipe uses `false` because saving a new document is a write operation.
- `M:TFlex.Application.NewDocument(System.Boolean,System.Boolean)` — create a new hidden 2D document with `b3D=false`, `visible=false`.
- `M:TFlex.Model.Document.SaveAs(System.String)` — save the document to a `.grb` path and return success state.
- `P:TFlex.Model.Document.FileName` — verify the saved document has a concrete file path.
- `P:TFlex.Model.Document.FilePath` — observe the saved directory.
- `P:TFlex.Model.Document.Title` — observe title before/after save.
- `M:TFlex.Model.Document.Close` — close the temporary document.
- `M:TFlex.Application.ExitSession` — paired session cleanup.

## C# Source

See `agent_workspace/recipes/save_document_as_temp.cs`.

## Verification

Expected live stdout shape:

```text
init=True
docNull=False
saved=True
exists=True
output=...
fileNameAfter=...
filePathAfter=...
artifactMarker=...
session=False
```

The live tests assert:

- `SaveAs` returned `true`;
- output `.grb` exists and is non-empty;
- `Document.FileName` is populated after save;
- `TFLEX_HARNESS_ARTIFACTS_DIR` marker is reported through runner artifacts.

## Assumptions

- T-FLEX CAD 17 is installed at `C:\Program Files\T-FLEX CAD 17`.
- The external process can obtain the `TFlexAPI` license.
- `PATH` includes `C:\Program Files\T-FLEX CAD 17\Program` at runtime so native dependencies load.

## Limitations

- The recipe creates and saves a new empty hidden 2D document only.
- It does not save or mutate any existing user document.
- It does not test format export beyond native `.grb` save.
