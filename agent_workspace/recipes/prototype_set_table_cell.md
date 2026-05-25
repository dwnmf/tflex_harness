# Recipe: prototype_set_table_cell

## Purpose

Copy one installed T-FLEX `.grb` prototype into the run artifact directory, open the copy, set one cell in the first table-bearing `RichText`, save a new `.grb`, reopen it, and verify the cell text persisted.

This is Phase 4 table/text mutation for prototype-driven document generation.

## Documentation Evidence

Docs used:

- `D:\REALPROJECTS\tflex_api\llm\symbols.jsonl`
- `T:TFlex.Model.Model2D.RichText`
- `M:TFlex.Model.Model2D.RichText.BeginEdit`
- `M:TFlex.Model.Model2D.RichText.EndEdit`
- `M:TFlex.Model.Model2D.RichText.GetTableByIndex(System.UInt32)`
- `T:TFlex.Model.Model2D.Table`
- `M:TFlex.Model.Model2D.Table.GetCellText(System.UInt32)`
- `M:TFlex.Model.Model2D.Table.Clear(System.UInt32)`
- `M:TFlex.Model.Model2D.Table.InsertText(System.UInt32,System.UInt32,System.String)`
- `M:TFlex.Model.Document.BeginChanges`, `M:TFlex.Model.Document.EndChanges`.

## C# Source

Snippet: `agent_workspace/recipes/prototype_set_table_cell.cs`

This recipe compiles with helper source set `easy_text` from `src/tflex_harness/csharp_helpers`.

Input:

```text
TFLEX_PROTOTYPE_SOURCE_PATH=<absolute path to source .grb prototype>
TFLEX_TABLE_CELL_INDEX=<zero-based uint cell index in first table>
TFLEX_TABLE_CELL_TEXT=<new cell text>
```

Harness recipe args:

```text
source_path=<absolute .grb path>
prototype_id=<catalog id, optional when source_path is provided>
prototype_selector=<catalog id/name/relative path alias, optional>
cell_index=<zero-based cell index>
text_value=<new value>
```

## Live Verification Report

Test: `prototype_set_table_cell`

Docs used:

- `D:\REALPROJECTS\tflex_api\llm\types\TFlexAPI__TFlex.Model.Model2D.RichText__*.md`
- `D:\REALPROJECTS\tflex_api\llm\types\TFlexAPI__TFlex.Model.Model2D.Table__*.md`
- Live probe `artifacts/runs/20260525_181032_642399_rich_text_probe` to confirm the first `RichText` in the gear-parameters table has editable table cells.

Snippet: `agent_workspace/recipes/prototype_set_table_cell.cs`

Result: pass.

Evidence:

- live run directory: `artifacts/runs/20260525_181242_346840_recipe_prototype_set_table_cell`;
- command: `python -m tflex_harness.cli run-recipe prototype_set_table_cell --arg 'prototype_id=Таблицы/Таблица параметров зубчатого колеса.grb' --arg 'cell_index=2' --arg 'text_value=Harness Table Test' --timeout-sec 120`;
- source prototype: `C:\Program Files\T-FLEX CAD 17\Program\Прототипы\Таблицы\Таблица параметров зубчатого колеса.grb`;
- stdout: `richText.count=1`;
- stdout: `table.cell.index=2`;
- stdout: `table.cell.before=`;
- stdout: `table.cell.after=Harness Table Test`;
- stdout: `endChanges=OK`;
- stdout: `table.cell.set=True`;
- stdout: `document.saved=True`;
- stdout: `table.cell.reopened=Harness Table Test`;
- stdout: `table.cell.persisted=True`;
- stdout: `easy.session=False`;
- run returned exit code `0`.

Blockers: none for the verified cell `2` in `Таблица параметров зубчатого колеса.grb`.

## Assumptions

- The prototype has at least one `RichText` with a table at index `0`.
- Cell indices are zero-based T-FLEX table cell indices.
- The recipe writes only into `TFLEX_HARNESS_ARTIFACTS_DIR`.


Batch table/specification probes:

- command: `python -m tflex_harness.cli prototypes-table-cell-batch --category Таблицы --timeout-sec 120 --fail-fast`;
- table matrix: `artifacts/prototype_validation/20260525_220550_733488/prototype_table_cell_matrix.json`;
- table result: selected `7`, attempted `7`, passed `7`, failed `0`, persisted `7`;
- command: `python -m tflex_harness.cli prototypes-table-cell-batch --category Спецификации --timeout-sec 120`;
- specification matrix: `artifacts/prototype_validation/20260525_220918_092578/prototype_table_cell_matrix.json`;
- specification result: selected `20`, attempted `20`, passed `1`, failed `19`, persisted `1`;
- result interpretation: installed `Таблицы/*` prototypes expose mutable `RichText` table cells through this API path; most installed `Спецификации/*` prototypes need a richer specification-specific API path.

## Limitations

- This recipe targets the first table in the first `RichText`.
- It clears the target cell before inserting new plain text.
- It does not preserve rich formatting inside the edited cell.
