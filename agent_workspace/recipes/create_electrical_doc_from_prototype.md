# Recipe: create_electrical_doc_from_prototype

## Purpose

Create an electrical document from the installed terminal-block prototype, replace visible text, save, reopen, and verify.

Phase 5 category recipe. Source remains visible C# and helper source set `easy_text`.

## Documentation Evidence

Docs used:

- `D:\REALPROJECTS\tflex_api\llm\symbols.jsonl`
- Existing verified prototype mutation helper recipe for this category path.

## C# Source

Snippet: `agent_workspace/recipes/create_electrical_doc_from_prototype.cs`

Default prototype: `Электротехника/Клеммник.grb`

Default target: `search_text=Цепь`

Default value: `Harness Electrical Circuit`

## Live Verification Report

Test: `create_electrical_doc_from_prototype`

Docs used:

- Existing verified prototype mutation helper recipe for the same API path.

Snippet: `agent_workspace/recipes/create_electrical_doc_from_prototype.cs`

Result: live verification passed.

Evidence:

- run: `artifacts/runs/20260525_213241_046854_recipe_create_electrical_doc_from_prototype`
- source: `C:\Program Files\T-FLEX CAD 17\Program\Прототипы\Электротехника\Клеммник.grb`
- stdout: `visibleText.replaceCount=1`, `document.saved=True`, `document.outputSize=58724`, `visibleText.newAfter=1`, `visibleText.persisted=True`

Blockers: none for this live path.

## Limitations

- First category recipe pass. It proves safe open/copy/mutate/save/reopen for this category.
- It does not yet expose every category-specific semantic field.
