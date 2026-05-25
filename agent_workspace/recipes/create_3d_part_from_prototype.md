# Recipe: create_3d_part_from_prototype

## Purpose

Create a 3D part from the installed 3D part prototype, set Title, save, reopen, and verify.

Phase 5 category recipe. Source remains visible C# and helper source set `easy_document_properties`.

## Documentation Evidence

Docs used:

- `D:\REALPROJECTS\tflex_api\llm\symbols.jsonl`
- Existing verified prototype mutation helper recipe for this category path.

## C# Source

Snippet: `agent_workspace/recipes/create_3d_part_from_prototype.cs`

Default prototype: `3D Деталь`

Default target: `Title`

Default value: `Harness 3D Part`

## Live Verification Report

Test: `create_3d_part_from_prototype`

Docs used:

- Existing verified prototype mutation helper recipe for the same API path.

Snippet: `agent_workspace/recipes/create_3d_part_from_prototype.cs`

Result: live verification passed.

Evidence:

- run: `artifacts/runs/20260525_213236_790332_recipe_create_3d_part_from_prototype`
- source: `C:\Program Files\T-FLEX CAD 17\Program\Прототипы\3D Деталь.grb`
- stdout: `documentProperty.after.Title=Harness 3D Part`, `document.saved=True`, `document.outputSize=28573`, `documentProperty.persisted=True`

Blockers: none for this live path.

## Limitations

- First category recipe pass. It proves safe open/copy/mutate/save/reopen for this category.
- It does not yet expose every category-specific semantic field.
