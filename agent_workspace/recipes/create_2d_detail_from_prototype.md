# Recipe: create_2d_detail_from_prototype

## Purpose

Create a 2D detail from the installed 2D detail prototype, set Title, save, reopen, and verify.

Phase 5 category recipe. Source remains visible C# and helper source set `easy_document_properties`.

## Documentation Evidence

Docs used:

- `D:\REALPROJECTS\tflex_api\llm\symbols.jsonl`
- Existing verified helper recipe `prototype_set_document_property`.

## C# Source

Snippet: `agent_workspace/recipes/create_2d_detail_from_prototype.cs`

Default prototype: `2D Деталь`

Default target: `Title`

Default value: `Harness 2D Detail`

## Live Verification Report

Test: `create_2d_detail_from_prototype`

Docs used:

- Existing verified helper recipe `prototype_set_document_property`.

Snippet: `agent_workspace/recipes/create_2d_detail_from_prototype.cs`

Result: pass.

Evidence:

- live run directory: `artifacts/runs/20260525_214436_007919_recipe_create_2d_detail_from_prototype`;
- command: `python -m tflex_harness.cli run-recipe create_2d_detail_from_prototype --timeout-sec 120`;
- source prototype: `C:\Program Files\T-FLEX CAD 17\Program\Прототипы\2D Деталь.grb`;
- category default property: `Title`;
- category default value: `Harness 2D Detail`;
- stdout: `document.opened=True`;
- stdout: `documentProperty.exists=True`;
- stdout: `documentProperty.after.Title=Harness 2D Detail`;
- stdout: `endChanges=OK`;
- stdout: `documentProperty.set=True`;
- stdout: `document.saved=True`;
- stdout: `document.outputSize=23230`;
- stdout: `documentProperty.reopened=Harness 2D Detail`;
- stdout: `documentProperty.persisted=True`;
- stdout: `easy.session=False`;
- run returned exit code `0`.

Blockers: none for this verified document-property path.

## Limitations

- This recipe edits a writable document property only.
- It does not yet expose deeper category-specific semantics.
