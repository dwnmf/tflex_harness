# T-FLEX Harness Goal: Point Fixes 1-3

Date: 2026-05-26

This file records the completed point-fix goal for installed T-FLEX prototype documents and fragment LCS factory payloads. Old broad phase history is intentionally removed.

## Non-Negotiables Satisfied

- Visible C# snippets plus checked-in helper source files; no hidden wrapper DLLs.
- `C:\Program Files\T-FLEX CAD 17\Program\Прототипы` used as reference coverage only.
- All mutations ran on copied `.grb` files under `artifacts/runs/...`.
- Verification used narrow live T-FLEX runs, not broad/unit test drag.
- Evidence saved under `artifacts/runs/...`, `artifacts/prototype_validation/...`, and `artifacts/document_factory_batches/...`.
- Recipe docs/metadata, README, and skill were updated.

## Point Fix 1: Specifications via BOMObject

### Completed Live

- Probe found real spec object model: `TFlex.Model.Model2D.BOMObject`.
- Probe evidence: `artifacts/runs/20260526_210936_525247_recipe_prototype_probe_specification_objects`.
- Helper: `src/tflex_harness/csharp_helpers/TFlexEasySpecifications.cs`.
- Recipe: `agent_workspace/recipes/prototype_set_specification_bom_field.cs`.
- Verification scans all BOM records after reopen, not only the first record.
- Single proof on former failing template:
  - run: `artifacts/runs/20260526_212003_622190_recipe_prototype_set_specification_bom_field`;
  - evidence: `spec.scan.2.field=Harness Spec Scan`, `spec.field.reopenedAny=True`, `spec.field.persisted=True`.
- Category matrix:
  - matrix: `artifacts/prototype_validation/20260526_212016_705556/prototype_specification_bom_field_matrix.json`;
  - result: selected `20`, attempted `20`, passed `20`, failed `0`, persisted `20`;
  - bucket: `bom_standard_field_supported=20`.

## Point Fix 2: Electrical Labels

### Completed Live

- Generic visible text path remains proven for easy electrical templates: `artifacts/runs/20260525_220841_828547_recipe_prototype_replace_first_visible_text`, `firstVisibleText.persisted=True`.
- Probe: `agent_workspace/recipes/prototype_probe_electrical_objects.cs`.
- Probe live run on previously failed `Электротехника/Аппарат`:
  - run: `artifacts/runs/20260526_212519_855910_recipe_prototype_probe_electrical_objects`;
  - finding: variable-backed template with `$Наименование`, `$Обозначение`, `$Tip_Doc`, `$Vid`.
- Existing variable helper proven as semantic electrical path:
  - recipe: `prototype_set_text_variable`;
  - run: `artifacts/runs/20260526_212542_998623_recipe_prototype_set_text_variable`;
  - evidence: `variable.exists=True`, `variable.expression.$Наименование="Harness Electrical Name"`, `variable.reopened=Harness Electrical Name`, `variable.persisted=True`.
- Electrical category fallback/classification batch added:
  - command: `python -m tflex_harness.cli prototypes-electrical-labels-batch --category Электротехника --timeout-sec 120`;
  - matrix: `artifacts/prototype_validation/20260526_213248_774110/prototype_electrical_labels_matrix.json`;
  - result: selected `8`, attempted `8`, passed `8`, failed `0`, persisted `8`;
  - buckets: `visible_text_supported=4`, `variable_backed_supported=4`.

## Point Fix 3: Fragment LCS Factory Payload

### Completed Live

- Standalone native path remains proven:
  - recipe: `helper_fragment_lcs_assembly`;
  - run: `artifacts/runs/20260525_220748_356485_recipe_helper_fragment_lcs_assembly`;
  - evidence: `fragment.sourceLcs=FRAG_LCS`, `fragment.targetLcsNull=False`, `assembly.operationsAfter=1`, `assembly.saved=True`, `fragmentAssembly.persisted=True`.
- Factory payload type added: `document.fragment_lcs_assembly`.
- Sample payload added: `agent_workspace/payloads/fragment_lcs_assembly.json`.
- Payload supports source part stem, assembly stem, source LCS name, target LCS name, target position in mm, target Z rotation, source block size, and optional STEP export.
- Direct live factory proof:
  - command: `python -m tflex_harness.cli create-document --payload agent_workspace/payloads/fragment_lcs_assembly.json --timeout-sec 120`;
  - factory run: `artifacts/runs/20260526_213859_133554_document_factory`;
  - recipe run: `artifacts/runs/20260526_213859_145299_factory_fragment_lcs_assembly`;
  - evidence: `factory.fragment.sourceLcsAfterFix=FRAG_LCS`, `factory.fragment.targetLcsNullAfterFix=False`, `factory.fragment.assemblyOperationsAfter=1`, `factory.fragment.reopened=True`, `factory.fragment.reopenedOperations=1`, `factory.fragment.persisted=True`;
  - outputs: `factory_fragment_lcs_assembly.grb` and `factory_fragment_lcs_assembly.step`.
- Batch live proof:
  - command: `python -m tflex_harness.cli document-factory-batch --payload-dir agent_workspace/payloads --timeout-sec 120`;
  - matrix: `artifacts/document_factory_batches/20260526_213924_474008/document_factory_batch_matrix.json`;
  - result: selected `1`, attempted `1`, passed `1`, failed `0`;
  - output formats: `grb`, `step`.

## Final State

- Point Fix 1 complete.
- Point Fix 2 complete.
- Point Fix 3 complete.
- No remaining work in this goal file.
