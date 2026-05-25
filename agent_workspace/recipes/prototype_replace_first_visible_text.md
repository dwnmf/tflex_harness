# Recipe: prototype_replace_first_visible_text

## Purpose

Copy an installed `.grb` prototype, open the copy, replace the first visible non-table 2D text object, save a new `.grb`, reopen it, and verify persistence.

## Documentation Evidence

Docs used:

- Existing verified helper recipe `prototype_replace_visible_text`.
- `TFlexEasyText.FirstVisibleText` / `TFlexEasyText.ReplaceFirstVisibleText` helper source.

## C# Source

Snippet: `agent_workspace/recipes/prototype_replace_first_visible_text.cs`

## Live Verification Report

Test: `prototype_replace_first_visible_text`

Docs used:

- Existing verified helper recipe `prototype_replace_visible_text`.

Snippet: `agent_workspace/recipes/prototype_replace_first_visible_text.cs`

Result: pass.

Evidence:

- live run directory: `artifacts/runs/20260525_220841_828547_recipe_prototype_replace_first_visible_text`;
- command: `python -m tflex_harness.cli run-recipe prototype_replace_first_visible_text --arg 'prototype_id=Электротехника/Клеммник.grb' --arg 'text_value=Harness First Visible Direct' --timeout-sec 120`;
- source prototype: `C:\Program Files\T-FLEX CAD 17\Program\Прототипы\Электротехника\Клеммник.grb`;
- stdout: `firstVisibleText.before=Цепь`;
- stdout: `firstVisibleText.kind=LineText`;
- stdout: `firstVisibleText.after=Harness First Visible Direct`;
- stdout: `endChanges=OK`;
- stdout: `firstVisibleText.set=True`;
- stdout: `document.saved=True`;
- stdout: `document.outputSize=58725`;
- stdout: `firstVisibleText.reopened=Harness First Visible Direct`;
- stdout: `firstVisibleText.persisted=True`;
- run returned exit code `0`.

Batch electrical probe:

- command: `python -m tflex_harness.cli prototypes-first-visible-text-batch --category Электротехника --timeout-sec 120`;
- matrix: `artifacts/prototype_validation/20260525_220808_834096/prototype_first_visible_text_matrix.json`;
- selected: `8`, attempted: `8`, passed: `4`, failed: `4`, persisted: `4`;
- passed prototypes: `Клеммник`, `Микросхема`, `Однолинейная схема`, `Соединитель`.

Blockers: four electrical prototypes had no API-visible non-table text for this helper path.

## Limitations

- Replaces the first non-empty visible `LineText` or non-table `RichText` only.
- Does not yet mutate electrical symbol geometry or connectivity semantics.
