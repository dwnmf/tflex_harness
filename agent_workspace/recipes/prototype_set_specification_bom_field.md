# Recipe: prototype_set_specification_bom_field

Copy/open a specification prototype, set a standard field on the first `BOMObject` record, save, reopen, and verify persistence.

This is the specification-specific path discovered by `prototype_probe_specification_objects`: specification prototypes expose `TFlex.Model.Model2D.BOMObject`, not a plain first `RichText` table.

## Usage

```powershell
python -m tflex_harness.cli run-recipe prototype_set_specification_bom_field --arg 'prototype_id=Спецификации/Спецификация форма 1 ГОСТ 2.106-2019' --arg 'standard_field=Desc' --arg 'text_value=Harness Spec BOM Desc' --timeout-sec 120
```

## Live Verification Report

Test: `prototype_set_specification_bom_field`
Docs used: local T-FLEX API docs for `TFlex.Model.Model2D.BOMObject.UpdateStandardFieldValue`, `GetStandardFieldValue`, `BeginEdit`, `EndEdit`, `MoveToFrontRecord`, `UpdateRecord`.
Snippet: `agent_workspace/recipes/prototype_set_specification_bom_field.cs`
Result: passed live with `add_record=true`.
Evidence:

- command: `python -m tflex_harness.cli run-recipe prototype_set_specification_bom_field --arg 'prototype_id=Спецификации/Спецификация форма 1 ГОСТ 2.106-2019' --arg 'standard_field=Desc' --arg 'text_value=Harness Spec BOM Desc' --arg 'add_record=true' --timeout-sec 120`;
- live run directory: `artifacts/runs/20260526_211159_374848_recipe_prototype_set_specification_bom_field`;
- `spec.bom.exists=True`;
- `spec.record.added=True`;
- `spec.field.after=Harness Spec BOM Desc`;
- `spec.field.reopened=Harness Spec BOM Desc`;
- `spec.field.persisted=True`.

Batch evidence:

- command: `python -m tflex_harness.cli prototypes-specification-bom-field-batch --category Спецификации --timeout-sec 120`;
- matrix: `artifacts/prototype_validation/20260526_211323_125648/prototype_specification_bom_field_matrix.json`;
- result: selected `20`, attempted `20`, passed `17`, failed `3`, persisted `17`;
- buckets: `bom_standard_field_supported=17`, `bom_no_persist=3`.

Blockers: three installed specification-like templates still do not persist this `Desc` standard field path.
