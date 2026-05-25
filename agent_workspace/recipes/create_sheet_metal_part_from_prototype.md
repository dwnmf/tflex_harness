# Recipe: create_sheet_metal_part_from_prototype

## Purpose

Create a sheet-metal part from the installed sheet-metal part prototype, set Title, save, reopen, and verify.

Phase 5 category recipe. Source remains visible C# and helper source set `easy_document_properties`.

## Documentation Evidence

Docs used:

- `D:\REALPROJECTS\tflex_api\llm\symbols.jsonl`
- Existing verified helper recipe `prototype_set_document_property`.

## C# Source

Snippet: `agent_workspace/recipes/create_sheet_metal_part_from_prototype.cs`

Default prototype: `Листовая Деталь`

Default target: `Title`

Default value: `Harness Sheet Metal Part`

## Live Verification Report

Test: `create_sheet_metal_part_from_prototype`

Docs used:

- Existing verified helper recipe `prototype_set_document_property`.

Snippet: `agent_workspace/recipes/create_sheet_metal_part_from_prototype.cs`

Result: pass.

Evidence:

- live run directory: `artifacts/runs/20260525_214438_176369_recipe_create_sheet_metal_part_from_prototype`;
- command: `python -m tflex_harness.cli run-recipe create_sheet_metal_part_from_prototype --timeout-sec 120`;
- source prototype: `C:\Program Files\T-FLEX CAD 17\Program\Прототипы\Листовая Деталь.grb`;
- category default property: `Title`;
- category default value: `Harness Sheet Metal Part`;
- stdout: `document.opened=True`;
- stdout: `documentProperty.exists=True`;
- stdout: `documentProperty.after.Title=Harness Sheet Metal Part`;
- stdout: `endChanges=OK`;
- stdout: `documentProperty.set=True`;
- stdout: `document.saved=True`;
- stdout: `document.outputSize=28418`;
- stdout: `documentProperty.reopened=Harness Sheet Metal Part`;
- stdout: `documentProperty.persisted=True`;
- stdout: `easy.session=False`;
- run returned exit code `0`.

Blockers: none for this verified document-property path.

## Limitations

- This recipe edits a writable document property only.
- It does not yet expose deeper category-specific semantics.
