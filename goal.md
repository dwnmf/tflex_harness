# T-FLEX Harness Goal: Point Fixes 1-3

Date: 2026-05-26

This file is the active short backlog. Old broad phases are intentionally removed. Work only on three point fixes needed to turn installed T-FLEX prototypes into reliable harness-driven documents.

## Non-Negotiables

- Use visible C# snippets plus checked-in helper source files; no hidden wrapper DLLs.
- Treat `C:\Program Files\T-FLEX CAD 17\Program\Прототипы` as reference coverage only.
- Mutate only copied `.grb` files under `artifacts/runs/...`.
- Do not run broad/unit test drag while time is low; use narrow live T-FLEX proof.
- Save evidence under `artifacts/runs/...` or `artifacts/prototype_validation/...`.
- Update recipe docs/metadata and this file when a path becomes live-proven.
- Commit and push each completed iteration.

## Baseline Already Proven

- Prototype discovery and copy/open/save work.
- `Document.Properties.Title` persists on all installed prototypes: `artifacts/prototype_validation/20260525_215002_183343/prototype_title_mutation_matrix.json` (`50/50`).
- Generic `RichText` table-cell mutation works for `Таблицы/*`: `artifacts/prototype_validation/20260525_220550_733488/prototype_table_cell_matrix.json` (`7/7`).
- Generic first visible text mutation works for some `Электротехника/*`: `artifacts/prototype_validation/20260525_220808_834096/prototype_first_visible_text_matrix.json` (`4/8`).
- Fragment insertion by `PointsLCS` + `Fragment3D.FixByFragmentLCS(...)` works standalone: `artifacts/runs/20260525_220748_356485_recipe_helper_fragment_lcs_assembly`.

## Point Fix 1: Specifications via BOMObject

### Done Live

- Probe found real spec object model: `TFlex.Model.Model2D.BOMObject`.
- Probe evidence: `artifacts/runs/20260526_210936_525247_recipe_prototype_probe_specification_objects`.
- Helper added: `src/tflex_harness/csharp_helpers/TFlexEasySpecifications.cs`.
- Recipe updated: `agent_workspace/recipes/prototype_set_specification_bom_field.cs`.
- Important fix: verification now scans all BOM records, not only the first record. This removed false `bom_no_persist` failures.
- Single proof on former failing template:
  - run: `artifacts/runs/20260526_212003_622190_recipe_prototype_set_specification_bom_field`;
  - evidence: `spec.scan.2.field=Harness Spec Scan`, `spec.field.reopenedAny=True`, `spec.field.persisted=True`.
- Category matrix:
  - matrix: `artifacts/prototype_validation/20260526_212016_705556/prototype_specification_bom_field_matrix.json`;
  - result: selected `20`, attempted `20`, passed `20`, failed `0`, persisted `20`;
  - bucket: `bom_standard_field_supported=20`.

### Remaining

- None for installed `Спецификации/*` coverage.
- Keep generic `RichText` table helper for `Таблицы/*`; use `BOMObject` path for `Спецификации/*`.

## Point Fix 2: Electrical Labels

### Done Live

- Generic visible text path remains proven for easy electrical templates: `artifacts/runs/20260525_220841_828547_recipe_prototype_replace_first_visible_text`, `firstVisibleText.persisted=True`.
- Probe added: `agent_workspace/recipes/prototype_probe_electrical_objects.cs`.
- Probe live run on a previously failed template:
  - prototype: `Электротехника/Аппарат`;
  - run: `artifacts/runs/20260526_212519_855910_recipe_prototype_probe_electrical_objects`;
  - evidence: document has text variables like `$Наименование`, `$Обозначение`, `$Tip_Doc`, `$Vid`, plus geometry/control objects and no normal visible `LineText`/`RichText` label path.
- Existing variable helper proven as the semantic electrical path:
  - recipe: `prototype_set_text_variable`;
  - prototype: `Электротехника/Аппарат`;
  - run: `artifacts/runs/20260526_212542_998623_recipe_prototype_set_text_variable`;
  - evidence: `variable.exists=True`, `variable.expression.$Наименование="Harness Electrical Name"`, `variable.reopened=Harness Electrical Name`, `variable.persisted=True`.

### Remaining

1. Add/extend an electrical category batch that first tries visible text, then classifies variable-backed templates and applies `prototype_set_text_variable` where the target variable exists.
2. Run that batch only on `Электротехника/*` and report buckets:
   - `visible_text_supported`;
   - `variable_backed_supported`;
   - `symbol_property_backed`;
   - `unsupported_unknown`.
3. If any failing prototype is not variable-backed, add a focused probe for that exact template before creating another helper.

## Point Fix 3: Fragment LCS Factory Payload

### Done Live

- Standalone native path is proven:
  - recipe: `helper_fragment_lcs_assembly`;
  - run: `artifacts/runs/20260525_220748_356485_recipe_helper_fragment_lcs_assembly`;
  - evidence: `fragment.sourceLcs=FRAG_LCS`, `fragment.targetLcsNull=False`, `assembly.operationsAfter=1`, `assembly.saved=True`, `fragmentAssembly.persisted=True`.

### Remaining

1. Add a document factory payload type for fragment LCS assembly creation.
2. Payload must include source part stem, source LCS name, target LCS name, target position/orientation, assembly stem, optional STEP export.
3. Generated C# must use the proven path exactly:
   - create source part `.grb`;
   - create `PointsLCS` with `UseForFragment=true` and `UseForFragmentFixing=true`;
   - save/close source part;
   - create assembly document;
   - create target `PointsLCS`;
   - insert `Fragment3D`;
   - call `FixByFragmentLCS(sourceName, targetLcs)`;
   - save/reopen assembly.
4. Prove one JSON payload live via `document-factory-batch` or equivalent factory command.

## Next Work Order

1. Electrical batch with variable-backed classification.
2. Fragment LCS document-factory payload and one live factory proof.
3. Only after that, broaden prototype coverage if needed.
