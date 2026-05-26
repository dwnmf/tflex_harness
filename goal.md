# T-FLEX Harness Goal: Point Fixes 1-3

Date: 2026-05-26

This file is the only active plan. Old broad phase history is intentionally removed. Current work is narrow: fix three semantic gaps proven by live T-FLEX evidence, using only targeted live runs.

## Non-Negotiables

- Use visible C# snippets plus checked-in helper source files; no hidden wrapper DLLs.
- Use `C:\Program Files\T-FLEX CAD 17\Program\Прототипы` as reference coverage, not as files to mutate in place.
- Work only on artifact copies of `.grb` files.
- Do not run broad/unit test drag unless a code path truly needs it.
- Prefer one live T-FLEX proof for the exact changed path.
- Save evidence under `artifacts/runs/...` or `artifacts/prototype_validation/...`.
- Update recipe docs/metadata and this file when a path becomes live-proven.
- Commit and push each completed iteration.

## Current Baseline

Already live-proven:

- Installed prototype scan works.
- Copy/open/save works for installed `.grb` prototypes.
- `Document.Properties.Title` mutation works for all 50 installed prototypes.
- Generic `RichText` table-cell mutation works for `Таблицы/*`.
- Generic first visible 2D text replacement works for some `Электротехника/*` prototypes.
- Fragment insertion by `PointsLCS` + `Fragment3D.FixByFragmentLCS(...)` works as a standalone recipe.

Key evidence:

- Title batch: `artifacts/prototype_validation/20260525_215002_183343/prototype_title_mutation_matrix.json` (`50/50`, persisted `50`).
- Tables batch: `artifacts/prototype_validation/20260525_220550_733488/prototype_table_cell_matrix.json` (`7/7`, persisted `7`).
- Specification weak batch: `artifacts/prototype_validation/20260525_220918_092578/prototype_table_cell_matrix.json` (`1/20`, persisted `1`).
- Electrical visible text batch: `artifacts/prototype_validation/20260525_220808_834096/prototype_first_visible_text_matrix.json` (`4/8`, persisted `4`).
- Electrical direct proof: `artifacts/runs/20260525_220841_828547_recipe_prototype_replace_first_visible_text` (`firstVisibleText.persisted=True`).
- Fragment LCS proof: `artifacts/runs/20260525_220748_356485_recipe_helper_fragment_lcs_assembly` (`fragmentAssembly.persisted=True`).

## Point Fix 1: Specifications

### Problem

`Таблицы/*` works through generic `RichText.GetTableByIndex(0)` cell mutation. Most `Спецификации/*` prototypes fail through that same path with `InvalidOperationException: Can not find object` or `Bad position`.

### Next Exact Work

1. Add a specification probe recipe/snippet that opens one copied failing `Спецификации/*` prototype and prints:
   - 2D object type histogram;
   - object names where readable;
   - reflected public members containing `Spec`, `Table`, `Cell`, `Row`, `Text`, `Value`, `Data`;
   - writable text-like/table-like properties;
   - safe `RichText` table access results with per-object errors.
2. Run it live on at least one currently failing specification prototype.
3. From evidence, choose one writable path:
   - real specification API row/cell field;
   - variable-backed field;
   - property-backed field;
   - unsupported with proved object model reason.
4. Add the smallest helper only for the proven path.
5. Add a recipe named around the proven behavior, e.g. `prototype_set_specification_cell` or `prototype_set_specification_field`.
6. Run a narrow live persist/reopen proof.
7. Then rerun category matrix for `Спецификации` only if the single path works.

### Done

- At least one common `Спецификации/*` prototype has a persisted semantic mutation after reopen, or the failure is classified with concrete reflected API evidence.
- Matrix/report separates supported and unsupported spec templates.

## Point Fix 2: Electrical Labels

### Problem

`prototype_replace_first_visible_text` works only where visible labels are exposed as `LineText` or non-table `RichText`. Four electrical prototypes still fail:

- `Электротехника/Аппарат`
- `Электротехника/Базовый компонент`
- `Электротехника/Контактор`
- `Электротехника/Схема`

### Next Exact Work

1. Add an electrical metadata probe recipe/snippet for one failing prototype.
2. Print:
   - 2D object type histogram;
   - writable reflected members containing `Text`, `Name`, `Value`, `Mark`, `Label`, `Reference`, `Variable`, `Connector`, `Contact`;
   - document variables and text-like values;
   - symbol/block-like objects and writable properties.
3. Run it live on one failing electrical prototype.
4. Classify storage:
   - visible text;
   - variable-backed label;
   - symbol/property-backed label;
   - unsupported/unknown API.
5. Add one helper only after a persisted live mutation path is proven.
6. Extend the electrical batch output with classification buckets instead of plain failed rows.

### Done

- At least one currently failing electrical prototype is mutated semantically and persists after reopen, or has a proved unsupported classification.
- Batch matrix has explicit buckets.

## Point Fix 3: Fragment LCS Factory Payload

### Problem

`helper_fragment_lcs_assembly` proves the native T-FLEX path, but document factory payloads do not yet expose it.

### Next Exact Work

1. Add a document factory payload type for fragment LCS assembly creation.
2. Payload must include:
   - source part name/output path stem;
   - source LCS name;
   - target LCS name;
   - target position/orientation parameters;
   - assembly output stem;
   - optional STEP export flag.
3. Generate visible C# that uses the proven path:
   - create source part `.grb`;
   - create `PointsLCS` with `UseForFragment=true` and `UseForFragmentFixing=true`;
   - save/close part;
   - create assembly document;
   - create target `PointsLCS`;
   - insert `Fragment3D`;
   - call `FixByFragmentLCS(sourceName, targetLcs)`;
   - save assembly.
4. Validate live factory evidence:
   - part saved and non-empty;
   - assembly saved and non-empty;
   - `SourceLCSName` equals requested source LCS;
   - `TargetLCS` is non-null;
   - assembly operation count increased;
   - persisted reopen proof exists.

### Done

- `document-factory-batch` or equivalent factory command creates a part and assembly from one JSON payload live.
- Evidence includes persisted assembly proof matching the standalone recipe.

## Work Order

1. Specification probe and first proven mutation/classification.
2. Electrical probe and first proven mutation/classification.
3. Fragment LCS payload wiring and one live factory proof.

Stop after each pushed iteration if time is low.
