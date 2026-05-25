# Recipe: create_table_document_from_prototype

## Purpose

Create a table document from the installed gear-parameter table prototype, set one table cell, save, reopen, and verify.

Phase 5 category recipe. Source remains visible C# and helper source set `easy_text`.

## Documentation Evidence

Docs used:

- `D:\REALPROJECTS\tflex_api\llm\symbols.jsonl`
- Existing verified prototype mutation helper recipe for this category path.

## C# Source

Snippet: `agent_workspace/recipes/create_table_document_from_prototype.cs`

Default prototype: `Таблицы/Таблица параметров зубчатого колеса.grb`

Default target: `cell_index=2`

Default value: `Harness Table Document`

## Live Verification Report

Test: `create_table_document_from_prototype`

Docs used:

- Existing verified prototype mutation helper recipe for the same API path.

Snippet: `agent_workspace/recipes/create_table_document_from_prototype.cs`

Result: live verification passed.

Evidence:

- run: `artifacts/runs/20260525_213238_919912_recipe_create_table_document_from_prototype`
- source: `C:\Program Files\T-FLEX CAD 17\Program\Прототипы\Таблицы\Таблица параметров зубчатого колеса.grb`
- stdout: `richText.count=1`, `table.cell.after=Harness Table Document`, `document.saved=True`, `document.outputSize=63263`, `table.cell.persisted=True`

Blockers: none for this live path.

## Limitations

- First category recipe pass. It proves safe open/copy/mutate/save/reopen for this category.
- It does not yet expose every category-specific semantic field.
