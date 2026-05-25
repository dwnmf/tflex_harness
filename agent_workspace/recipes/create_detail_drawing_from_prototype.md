# Recipe: create_detail_drawing_from_prototype

## Purpose

Create a detail drawing document from the installed drawing prototype by copying the prototype, setting a writable document property, saving a new `.grb`, reopening it, and verifying persistence.

This is a Phase 5 category recipe for drawing documents. It intentionally uses visible C# plus `easy_document_properties`; no opaque CAD SDK wrapper is hidden.

## Documentation Evidence

Docs used:

- `D:\REALPROJECTS\tflex_api\llm\symbols.jsonl`
- `T:TFlex.Model.DocumentProperties`
- `P:TFlex.Model.Document.Properties`
- `P:TFlex.Model.DocumentProperties.Title`
- `M:TFlex.Model.Document.GetTextProperty(System.String)`.

## C# Source

Snippet: `agent_workspace/recipes/create_detail_drawing_from_prototype.cs`

This recipe compiles with helper source set `easy_document_properties`.

Harness recipe args:

```text
source_path=<absolute .grb path, optional>
prototype_id=<catalog id, defaults to Чертежи/Чертёж детали с форматкой>
prototype_selector=<catalog id/name/relative path alias, optional>
property_name=<writable string property, defaults to Title>
text_value=<new text, defaults to Harness Detail Drawing>
```

## Live Verification Report

Test: `create_detail_drawing_from_prototype`

Docs used:

- `D:\REALPROJECTS\tflex_api\llm\types\TFlexAPI__TFlex.Model.DocumentProperties__*.md`
- Existing verified helper recipe `prototype_set_document_property`.

Snippet: `agent_workspace/recipes/create_detail_drawing_from_prototype.cs`

Result: pass.

Evidence:

- live run directory: `artifacts/runs/20260525_212201_368610_recipe_create_detail_drawing_from_prototype`;
- command: `python -m tflex_harness.cli run-recipe create_detail_drawing_from_prototype --timeout-sec 120`;
- source prototype: `C:\Program Files\T-FLEX CAD 17\Program\Прототипы\Чертежи\Чертёж детали с форматкой.grb`;
- category default property: `Title`;
- category default value: `Harness Detail Drawing`;
- stdout: `document.opened=True`;
- stdout: `documentProperty.exists=True`;
- stdout: `documentProperty.after.Title=Harness Detail Drawing`;
- stdout: `endChanges=OK`;
- stdout: `documentProperty.set=True`;
- stdout: `document.saved=True`;
- stdout: `document.outputSize=25462`;
- stdout: `documentProperty.reopened=Harness Detail Drawing`;
- stdout: `documentProperty.persisted=True`;
- stdout: `easy.session=False`;
- run returned exit code `0`.

Blockers: none for the verified drawing prototype document-property path.

## Limitations

- This first category recipe edits a writable document property only.
- It does not yet fill title-block geometry-specific fields beyond API-visible `Document.Properties`.
- It does not export PDF/DXF/DWG itself; use document factory `output.exports` for exports.
