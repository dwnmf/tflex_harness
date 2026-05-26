# Recipe: prototype_probe_electrical_objects

Probe a copied electrical prototype and print live API evidence for labels, symbols, fragment variables, connectors, and circuit link objects.

## Purpose

Use this before adding electrical helpers. It does not mutate the prototype. It records:

- document variables;
- 2D object type histogram;
- reflected text/name/value/label/connector/contact/circuit members;
- fragment variable values, including internal variables when exposed;
- connector parameter names and values;
- all model object/circuit object histograms where `Document.GetObjects()` exposes them.

## Usage

```powershell
python -m tflex_harness.cli run-recipe prototype_probe_electrical_objects --arg 'prototype_id=Электротехника/Аппарат' --timeout-sec 120
```

## Live Verification Report

Test: `prototype_probe_electrical_objects`
Docs used: local T-FLEX API docs for `TFlex.Model.Model2D.Fragment`, `TFlex.Model.FragmentVariableValue`, `TFlex.Model.Model2D.Connector`, `TFlex.Model.ConnectorParameters`, `TFlex.Model.Circuits.Link`, `TFlex.Model.Circuits.LinkSymbol`; DeepWiki cross-check on electrical labels/fragments/connectors.
Snippet: `agent_workspace/recipes/prototype_probe_electrical_objects.cs`
Result: passed live, read-only probe.
Evidence:

- command: `python -m tflex_harness.cli run-recipe prototype_probe_electrical_objects --arg 'prototype_id=Электротехника/Аппарат' --timeout-sec 120`;
- live run directory: `artifacts/runs/20260526_212519_855910_recipe_prototype_probe_electrical_objects`;
- prototype: `C:\Program Files\T-FLEX CAD 17\Program\Прототипы\Электротехника\Аппарат.grb`;
- variables include `$Наименование`, `$Обозначение`, `$Tip_Doc`, `$Vid`, `$Cod_d`, `$Cod_d1`, `$Cod_d2`;
- model object histogram includes `TFlex.Model.Variable=66`, `TFlex.Model.Model2D.StaticTextControl=5`, `TFlex.Model.Model2D.EditControl=2`, structure objects, and construction objects;
- classification for `Электротехника/Аппарат`: variable-backed electrical template, not normal visible `LineText`/non-table `RichText`.

Follow-up mutation proof:

- recipe: `prototype_set_text_variable`;
- command: `python -m tflex_harness.cli run-recipe prototype_set_text_variable --arg 'prototype_id=Электротехника/Аппарат' --arg 'variable_name=$Наименование' --arg 'text_value=Harness Electrical Name' --timeout-sec 120`;
- run: `artifacts/runs/20260526_212542_998623_recipe_prototype_set_text_variable`;
- evidence: `variable.exists=True`, `variable.expression.$Наименование="Harness Electrical Name"`, `variable.reopened=Harness Electrical Name`, `variable.persisted=True`.

Blockers: none for variable-backed electrical prototypes with an existing target text variable.
