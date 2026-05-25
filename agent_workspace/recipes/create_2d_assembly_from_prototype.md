# Recipe: create_2d_assembly_from_prototype

## Purpose

Create a 2D assembly document from the installed 2D assembly prototype by copying the prototype, setting a writable document property, saving a new `.grb`, reopening it, and verifying persistence.

This is a Phase 5 category recipe. It intentionally uses visible C# plus `easy_document_properties`; no opaque CAD SDK wrapper is hidden.

## Documentation Evidence

Docs used:

- `D:\REALPROJECTS\tflex_api\llm\symbols.jsonl`
- `T:TFlex.Model.DocumentProperties`
- `P:TFlex.Model.Document.Properties`
- `P:TFlex.Model.DocumentProperties.Title`
- Existing verified helper recipe `prototype_set_document_property`.

## C# Source

Snippet: `agent_workspace/recipes/create_2d_assembly_from_prototype.cs`

This recipe compiles with helper source set `easy_document_properties`.

Harness recipe args:

```text
source_path=<absolute .grb path, optional>
prototype_id=<catalog id, defaults to 2D Сборка>
prototype_selector=<catalog id/name/relative path alias, optional>
property_name=<writable string property, defaults to Title>
text_value=<new text, defaults to Harness 2D Assembly>
```

## Live Verification Report

Test: `create_2d_assembly_from_prototype`

Docs used:

- Existing verified helper recipe `prototype_set_document_property`.

Snippet: `agent_workspace/recipes/create_2d_assembly_from_prototype.cs`

Result: pass.

Evidence:

- live run directory: `artifacts/runs/20260525_214103_281473_recipe_create_2d_assembly_from_prototype`;
- command: `python -m tflex_harness.cli run-recipe create_2d_assembly_from_prototype --timeout-sec 120`;
- source prototype: `C:\Program Files\T-FLEX CAD 17\Program\Прототипы\2D Сборка.grb`;
- category default property: `Title`;
- category default value: `Harness 2D Assembly`;
- stdout: `document.opened=True`;
- stdout: `documentProperty.exists=True`;
- stdout: `documentProperty.after.Title=Harness 2D Assembly`;
- stdout: `endChanges=OK`;
- stdout: `documentProperty.set=True`;
- stdout: `document.saved=True`;
- stdout: `document.outputSize=22489`;
- stdout: `documentProperty.reopened=Harness 2D Assembly`;
- stdout: `documentProperty.persisted=True`;
- stdout: `easy.session=False`;
- run returned exit code `0`.

Blockers: none for this verified document-property path.

## Limitations

- This first category recipe edits a writable document property only.
- It does not yet expose deeper category semantics.
