# Recipe: prototype_set_specification_bom_field

Copy/open a specification prototype, set a standard field on a `BOMObject` record, save, reopen, scan BOM records, and verify persistence.

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
- original live run directory: `artifacts/runs/20260526_211159_374848_recipe_prototype_set_specification_bom_field`;
- scan-based live run directory: `artifacts/runs/20260526_212003_622190_recipe_prototype_set_specification_bom_field`;
- `spec.bom.exists=True`;
- `spec.record.added=True`;
- `spec.field.after=Harness Spec BOM Desc`;
- original proof: `spec.field.reopened=Harness Spec BOM Desc`;
- scan proof: `spec.scan.2.field=Harness Spec Scan`;
- scan proof: `spec.field.reopenedAny=True`;
- `spec.field.persisted=True`.

Batch evidence:

- command: `python -m tflex_harness.cli prototypes-specification-bom-field-batch --category Спецификации --timeout-sec 120`;
- first matrix: `artifacts/prototype_validation/20260526_211323_125648/prototype_specification_bom_field_matrix.json`, selected `20`, passed `17`, failed `3`, persisted `17`;
- final scan-based matrix: `artifacts/prototype_validation/20260526_212016_705556/prototype_specification_bom_field_matrix.json`;
- final result: selected `20`, attempted `20`, passed `20`, failed `0`, persisted `20`;
- final buckets: `bom_standard_field_supported=20`.

Blockers: none for installed `Спецификации/*` prototypes after scan-based verification.
