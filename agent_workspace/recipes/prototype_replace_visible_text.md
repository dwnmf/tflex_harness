# Recipe: prototype_replace_visible_text

## Purpose

Copy one installed T-FLEX `.grb` prototype into the run artifact directory, open the copy, replace visible 2D text occurrences in `LineText` and non-table `RichText`, save a new `.grb`, reopen it, and verify the replacement persisted.

This is Phase 4 visible 2D text mutation for prototype-driven document generation.

## Documentation Evidence

Docs used:

- `D:\REALPROJECTS\tflex_api\llm\symbols.jsonl`
- `T:TFlex.Model.Model2D.LineText`
- `P:TFlex.Model.Model2D.LineText.TextValue`
- `T:TFlex.Model.Model2D.RichText`
- `P:TFlex.Model.Model2D.RichText.TextValue`
- `P:TFlex.Model.Model2D.RichText.TableOnly`
- `M:TFlex.Model.Model2D.RichText.BeginEdit`
- `M:TFlex.Model.Model2D.RichText.ClearAll`
- `M:TFlex.Model.Model2D.RichText.InsertText(System.String)`
- `M:TFlex.Model.Model2D.RichText.EndEdit`.

## C# Source

Snippet: `agent_workspace/recipes/prototype_replace_visible_text.cs`

This recipe compiles with helper source set `easy_text` from `src/tflex_harness/csharp_helpers`.

Input:

```text
TFLEX_PROTOTYPE_SOURCE_PATH=<absolute path to source .grb prototype>
TFLEX_VISIBLE_TEXT_SEARCH=<visible text to replace>
TFLEX_VISIBLE_TEXT_REPLACEMENT=<replacement text>
```

Harness recipe args:

```text
source_path=<absolute .grb path>
prototype_id=<catalog id, optional when source_path is provided>
prototype_selector=<catalog id/name/relative path alias, optional>
search_text=<required text to replace>
replacement_text=<replacement text, defaults to empty string>
```

## Live Verification Report

Test: `prototype_replace_visible_text`

Docs used:

- `D:\REALPROJECTS\tflex_api\llm\types\TFlexAPI__TFlex.Model.Model2D.LineText__*.md`
- `D:\REALPROJECTS\tflex_api\llm\types\TFlexAPI__TFlex.Model.Model2D.RichText__*.md`
- Live scan `artifacts/runs/20260525_182331_171078_visible_text_candidate_probe` showed `Электротехника/Клеммник.grb` has writable `LineText` with `TextValue=Цепь`.

Snippet: `agent_workspace/recipes/prototype_replace_visible_text.cs`

Result: pass.

Evidence:

- live run directory: `artifacts/runs/20260525_182531_611149_recipe_prototype_replace_visible_text`;
- command: `python -m tflex_harness.cli run-recipe prototype_replace_visible_text --arg 'prototype_id=Электротехника/Клеммник.grb' --arg 'search_text=Цепь' --arg 'replacement_text=Harness Circuit' --timeout-sec 120`;
- source prototype: `C:\Program Files\T-FLEX CAD 17\Program\Прототипы\Электротехника\Клеммник.grb`;
- stdout: `visibleText.search=Цепь`;
- stdout: `visibleText.beforeCount=1`;
- stdout: `visibleText.line.before=Цепь`;
- stdout: `visibleText.line.after=Harness Circuit`;
- stdout: `visibleText.replaced=1`;
- stdout: `endChanges=OK`;
- stdout: `visibleText.replaceCount=1`;
- stdout: `document.saved=True`;
- stdout: `visibleText.oldAfter=0`;
- stdout: `visibleText.newAfter=1`;
- stdout: `visibleText.persisted=True`;
- stdout: `easy.session=False`;
- run returned exit code `0`.

Blockers: none for the verified `LineText` replacement in `Клеммник.grb`.

## Assumptions

- The target visible text exists in `LineText` or non-table `RichText`.
- The recipe writes only into `TFLEX_HARNESS_ARTIFACTS_DIR`.

## Limitations

- `LineText` replacement preserves the text object and changes only `TextValue`.
- Non-table `RichText` replacement rewrites the whole rich text as plain text; formatting may be lost.
- Table text replacement uses `prototype_set_table_cell`.
