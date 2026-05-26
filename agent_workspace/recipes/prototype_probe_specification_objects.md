# Recipe: prototype_probe_specification_objects

Probe a copied specification prototype and print live API evidence for semantic mutation work.

## Purpose

Use this before adding specification helpers. It does not mutate the prototype. It records:

- 2D object type histogram;
- reflected table/spec/BOM/text/cell/row members;
- safe `RichText.GetTableByIndex(0)` evidence;
- `BOMObject` fields and current first-record values;
- active `ProductStructure`, scheme, rows, and row cells where available;
- document variables.

## Usage

```powershell
python -m tflex_harness.cli run-recipe prototype_probe_specification_objects --arg 'prototype_id=Спецификации/Спецификация форма 1 ГОСТ 2.106-2019' --timeout-sec 120
```

## Live Verification Report

Test: `prototype_probe_specification_objects`
Docs used: local T-FLEX API docs for `TFlex.Model.Model2D.BOMObject`, `TFlex.Model.ProductStructure`, `TFlex.Model.RowElement`, `TFlex.Model.RowElementCell`, `TFlex.Model.Model2D.RichText`.
Snippet: `agent_workspace/recipes/prototype_probe_specification_objects.cs`
Result: passed live on `Спецификации/Спецификация форма 1 ГОСТ 2.106-2019`.
Evidence:

- command: `python -m tflex_harness.cli run-recipe prototype_probe_specification_objects --arg 'prototype_id=Спецификации/Спецификация форма 1 ГОСТ 2.106-2019' --timeout-sec 120`;
- live run directory: `artifacts/runs/20260526_210936_525247_recipe_prototype_probe_specification_objects`;
- `richText.0.table.0.error=InvalidOperationException: Can not find object / Bad position`;
- `object.6.type=TFlex.Model.Model2D.BOMObject`;
- `bom.0.visibleField.count=7`;
- `bom.0.allField.count=44`;
- `productStructure.active=False`.
Blockers: none yet.
