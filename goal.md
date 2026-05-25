# T-FLEX Harness Goal: Targeted Fixes For Items 1-3

Date: 2026-05-25

This file is now intentionally compact. Old phase history was removed. Current work focuses only on three targeted fix tracks discovered by live T-FLEX evidence.

## Current Baseline

The harness can already do the safe generic paths:

- scan installed prototypes from `C:\Program Files\T-FLEX CAD 17\Program\Прототипы`;
- copy/open/save all installed `.grb` prototypes from artifact copies;
- mutate `Document.Properties.Title` across all 50 installed `.grb` prototypes;
- run visible C# snippets with helper source files, not hidden wrapper DLLs;
- write run evidence under `artifacts/runs/...` and matrices under `artifacts/prototype_validation/...`.

Recent live baseline:

- `prototypes-title-batch --timeout-sec 120 --fail-fast`: selected `50`, attempted `50`, passed `50`, failed `0`, persisted `50`.
- Matrix: `artifacts/prototype_validation/20260525_215002_183343/prototype_title_mutation_matrix.json`.

## Active Objective

Make the harness useful beyond safe generic `Title` mutation by fixing the three weak semantic areas:

1. Tables and specifications.
2. Electrical documents.
3. Fragments and assemblies.

Do this iteratively. Every meaningful fix must have live T-FLEX evidence before it is called done.

## Hard Validation Rule

No broad test drag unless explicitly needed. Prefer direct live checks:

```powershell
python -m tflex_harness.cli run-recipe <recipe> --timeout-sec 120
python -m tflex_harness.cli prototypes-table-cell-batch --category <category> --timeout-sec 120
python -m tflex_harness.cli prototypes-first-visible-text-batch --category <category> --timeout-sec 120
```

Use `git diff --check` and recipe freshness checks before commits. Push every completed iteration.

## Item 1: Tables And Specifications

### What Works Now

Generic `RichText` table-cell mutation works for installed `Таблицы/*` prototypes.

Live evidence:

- Command: `python -m tflex_harness.cli prototypes-table-cell-batch --category Таблицы --timeout-sec 120 --fail-fast`.
- Matrix: `artifacts/prototype_validation/20260525_220550_733488/prototype_table_cell_matrix.json`.
- Result: selected `7`, attempted `7`, passed `7`, failed `0`, persisted `7`.

### What Is Broken / Weak

Most installed `Спецификации/*` prototypes do not work through the same raw `RichText.GetTableByIndex(0)` / cell index path.

Live evidence:

- Command: `python -m tflex_harness.cli prototypes-table-cell-batch --category Спецификации --timeout-sec 120`.
- Matrix: `artifacts/prototype_validation/20260525_220918_092578/prototype_table_cell_matrix.json`.
- Result: selected `20`, attempted `20`, passed `1`, failed `19`, persisted `1`.
- Failure evidence includes `InvalidOperationException: Can not find object` / `Bad position` on specification table access.

### Targeted Fixes

1. Add a specification-specific probe that enumerates 2D objects and reflected members around specification/table objects, instead of assuming first `RichText` table.
2. Identify the real writable API for specification rows/cells.
3. Add helper source only after live proof of the writable path.
4. Add a recipe like `prototype_set_specification_cell` or `prototype_set_specification_row_field` only after the API path is proven.
5. Re-run against `Спецификации` category and record pass/fail matrix.

### Done Criteria

- At least one common `Спецификации/*` prototype has a live row/cell/field mutation that persists after reopen.
- The failure mode for unsupported specification templates is classified, not opaque.
- `README.md`, recipe markdown, and `goal.md` contain exact run dirs and matrix paths.

## Item 2: Electrical Documents

### What Works Now

Visible text replacement works on electrical prototypes that expose non-table `LineText` or non-table `RichText` through the 2D API.

Live evidence:

- Direct recipe: `prototype_replace_first_visible_text`.
- Direct run: `artifacts/runs/20260525_220841_828547_recipe_prototype_replace_first_visible_text`.
- Evidence: `firstVisibleText.before=Цепь`, `firstVisibleText.kind=LineText`, `firstVisibleText.after=Harness First Visible Direct`, `firstVisibleText.persisted=True`.

Batch evidence:

- Command: `python -m tflex_harness.cli prototypes-first-visible-text-batch --category Электротехника --timeout-sec 120`.
- Matrix: `artifacts/prototype_validation/20260525_220808_834096/prototype_first_visible_text_matrix.json`.
- Result: selected `8`, attempted `8`, passed `4`, failed `4`, persisted `4`.

### What Is Broken / Weak

Four electrical prototypes do not expose a simple first visible non-table text object via the current helper path.

Current failing/probably unsupported through this path:

- `Электротехника/Аппарат`
- `Электротехника/Базовый компонент`
- `Электротехника/Контактор`
- `Электротехника/Схема`

### Targeted Fixes

1. Add an electrical metadata probe that records 2D object type names, reflected writable text-like properties, and symbol-like object properties.
2. Find whether failing prototypes store labels in variables, object properties, hidden rich text, connector metadata, or electrical-specific API objects.
3. Add the smallest helper for the first proven semantic path.
4. Keep `prototype_replace_first_visible_text` as the generic visible-text path, but do not pretend it covers all electrical docs.
5. Create a matrix that separates:
   - visible-text supported;
   - variable-backed label supported;
   - symbol/property-backed label supported;
   - unsupported/needs deeper API.

### Done Criteria

- At least one currently failing electrical prototype has a live semantic mutation path that persists after reopen, or has a precise proved reason why no text/label mutation is available through current API.
- Electrical batch report has failure buckets, not just failed rows.
- Document factory can dispatch to the right electrical mutation helper when the payload requests it.

## Item 3: Fragments And Assemblies

### What Works Now

A semantic fragment insertion path is live-proven.

Recipe:

- `helper_fragment_lcs_assembly`

Live evidence:

- Run: `artifacts/runs/20260525_220748_356485_recipe_helper_fragment_lcs_assembly`.
- Evidence: `part.end=OK`, `source.useForFragment=True`, `fragment.sourceLcs=FRAG_LCS`, `fragment.targetLcsNull=False`, `assembly.operationsAfter=1`, `assembly.saved=True`, `fragmentAssembly.persisted=True`.

### What Is Broken / Weak

The current recipe is a standalone proof. It is not yet wired into the document factory payload model.

Missing pieces:

- payload schema for part/assembly creation;
- payload fields for source LCS, target LCS, placement coordinates;
- output contract for generated part `.grb` and assembly `.grb`;
- batch support for multiple fragments;
- optional STEP export for resulting assembly.

### Targeted Fixes

1. Add a document factory payload type for fragment LCS insertion.
2. Generate visible C# from payload using the already proven `PointsLCS` + `Fragment3D.FixByFragmentLCS` path.
3. Save both source part and assembly outputs under the factory run artifacts.
4. Validate operation count, `SourceLCSName`, non-null `TargetLCS`, and saved output sizes.
5. Add one live factory payload proof.

### Done Criteria

- `create-document --payload <fragment-assembly-payload.json>` creates a part and assembly live.
- Output includes named part `.grb` and assembly `.grb`.
- Evidence includes `fragmentAssembly.persisted=True` or equivalent factory validation fields.
- Optional later: STEP export of assembly if the generated assembly has exportable 3D bodies.

## Next Work Order

Do exactly this order unless new live evidence changes priority:

1. Specification-specific probe and mutation helper.
2. Electrical symbol/label metadata probe and first failing-prototype fix.
3. Fragment LCS insertion wired into document factory payload.

## Commit Discipline

For each iteration:

1. Run the narrow live command proving the exact path.
2. Update recipe metadata/docs and this file with run dirs.
3. Run `git diff --check`.
4. Commit.
5. Push.

Do not claim completion without live evidence.
