# Recipe: prototype_open_copy_save

## Purpose

Copy one installed T-FLEX `.grb` prototype into the run artifact directory, open the copy through live T-FLEX CAD, save it as a new `.grb`, close it, and print source/copy/output evidence.

This is the first prototype-driven document factory recipe. It proves the safe baseline: installed prototypes are read-only input, and all mutation happens on artifact copies.

## Documentation Evidence

Docs used:

- `D:\REALPROJECTS\tflex_api\llm\symbols.jsonl`
- `M:TFlex.Application.OpenDocument(System.String,System.Boolean,System.Boolean)` — open copied `.grb` with explicit visibility/read-only flags.
- `M:TFlex.Model.Document.SaveAs(System.String)` — save output `.grb`.
- `M:TFlex.Model.Document.Close` — close opened document.
- DeepWiki `dwnmf/tflex_api` cross-check for the open/save/close pattern.

## C# Source

Snippet: `agent_workspace/recipes/prototype_open_copy_save.cs`

This recipe compiles with helper source set `easy_prototype` from `src/tflex_harness/csharp_helpers`.

Input:

```text
TFLEX_PROTOTYPE_SOURCE_PATH=<absolute path to source .grb prototype>
```

Harness recipe args:

```text
source_path=<absolute .grb path>
prototype_id=<catalog id such as 3D Деталь>
prototype_selector=<catalog id/name/relative path>
```

## Live Verification Report

Test: `prototype_open_copy_save`

Docs used:

- `D:\REALPROJECTS\tflex_api\llm\symbols.jsonl`
- DeepWiki `dwnmf/tflex_api` answer for `Application.OpenDocument`, `Document.SaveAs`, and `Document.Close`.

Snippet: `agent_workspace/recipes/prototype_open_copy_save.cs`

Result: pass.

Evidence:

- live run directory: `artifacts/runs/20260525_172319_936833_prototype_open_copy_save_3d_part`;
- source prototype: `C:\Program Files\T-FLEX CAD 17\Program\Прототипы\3D Деталь.grb`;
- stdout: `prototype.sourceSha256=09d85579dbda002ceaf23e7f70c6c9ea2075143b6fe2f795026c643393dc7878`;
- stdout: `prototype.copySha256=09d85579dbda002ceaf23e7f70c6c9ea2075143b6fe2f795026c643393dc7878`;
- stdout: `document.opened=True`;
- stdout: `document.saved=True`;
- stdout: `document.outputSize=28544`;
- stdout: `document.closed=True`;
- stdout: `easy.session=False`;
- run returned exit code `0`.

Blockers: none for the verified `3D Деталь.grb` prototype.

## Assumptions

- T-FLEX CAD 17 is installed locally.
- The source prototype path exists and is readable.
- The recipe writes only into `TFLEX_HARNESS_ARTIFACTS_DIR`.

## Limitations

- This recipe proves safe open/copy/save. It does not yet fill title blocks, variables, specification rows, or tables.
- This recipe was live-verified on one root 3D prototype. Full 50-prototype batch validation is the next phase.
