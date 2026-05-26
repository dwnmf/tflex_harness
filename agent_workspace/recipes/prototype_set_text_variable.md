# Recipe: prototype_set_text_variable

## Purpose

Copy one installed T-FLEX `.grb` prototype into the run artifact directory, open the copy, set one existing text variable to a constant value, save a new `.grb`, reopen it, and verify the variable value persisted.

This is the first Phase 4 mutation recipe for prototype-driven document generation.

## Documentation Evidence

Docs used:

- `D:\REALPROJECTS\tflex_api\llm\symbols.jsonl`
- `T:TFlex.Model.Variable` for variable objects.
- `M:TFlex.Model.Document.GetVariables` from existing live state/metadata probes.
- `P:TFlex.Model.Variable.Expression`, `P:TFlex.Model.Variable.TextValue`, `P:TFlex.Model.Variable.IsText`.
- `M:TFlex.Model.Document.BeginChanges`, `M:TFlex.Model.Document.EndChanges`.
- `M:TFlex.Model.Document.SaveAs(System.String)`.

## C# Source

Snippet: `agent_workspace/recipes/prototype_set_text_variable.cs`

This recipe compiles with helper source set `easy_variables` from `src/tflex_harness/csharp_helpers`.

Input:

```text
TFLEX_PROTOTYPE_SOURCE_PATH=<absolute path to source .grb prototype>
TFLEX_VARIABLE_NAME=<existing text variable name>
TFLEX_VARIABLE_TEXT_VALUE=<new constant text value>
```

Harness recipe args:

```text
source_path=<absolute .grb path>
prototype_id=<catalog id, optional when source_path is provided>
prototype_selector=<catalog id/name/relative path alias, optional>
variable_name=<existing text variable name>
text_value=<new value>
```

PowerShell note: quote variable names containing `$` with single quotes so the shell does not expand them, for example `--arg 'variable_name=$Наименование'`.

## Live Verification Report

Test: `prototype_set_text_variable`

Docs used:

- `D:\REALPROJECTS\tflex_api\llm\types\TFlexAPI__TFlex.Model.Variable__*.md`
- Live metadata index `artifacts/prototype_metadata/live_all_20260525/metadata/001_2D.json` to choose `$Наименование`.

Snippet: `agent_workspace/recipes/prototype_set_text_variable.cs`

Result: pass.

Evidence:

- manual live run directory: `artifacts/runs/20260525_175227_326353_prototype_variable_mutation_live`;
- recipe live run directory: `artifacts/runs/20260525_175508_317973_recipe_prototype_set_text_variable`;
- recipe command: `python -m tflex_harness.cli run-recipe prototype_set_text_variable --arg 'prototype_id=2D Деталь' --arg 'variable_name=$Наименование' --arg 'text_value=Harness Recipe Test' --timeout-sec 120`;
- source prototype: `C:\Program Files\T-FLEX CAD 17\Program\Прототипы\2D Деталь.grb`;
- variable: `$Наименование`;
- stdout: `variable.exists=True`;
- stdout: `variable.expression.$Наименование="Harness Recipe Test"`;
- stdout: `endChanges=OK`;
- stdout: `variable.set=True`;
- stdout: `document.saved=True`;
- stdout: `variable.reopened=Harness Recipe Test`;
- stdout: `variable.persisted=True`;
- stdout: `easy.session=False`;
- run returned exit code `0`.

Blockers: none for the verified `$Наименование` text variable in `2D Деталь.grb`.


## Electrical Prototype Proof

Live on 2026-05-26 this same variable helper fixed a previously failed electrical prototype where visible `LineText`/`RichText` replacement did not apply.

Evidence:

- probe run: `artifacts/runs/20260526_212519_855910_recipe_prototype_probe_electrical_objects`;
- mutation run: `artifacts/runs/20260526_212542_998623_recipe_prototype_set_text_variable`;
- command: `python -m tflex_harness.cli run-recipe prototype_set_text_variable --arg 'prototype_id=Электротехника/Аппарат' --arg 'variable_name=$Наименование' --arg 'text_value=Harness Electrical Name' --timeout-sec 120`;
- stdout: `variable.exists=True`;
- stdout: `variable.expression.$Наименование="Harness Electrical Name"`;
- stdout: `variable.reopened=Harness Electrical Name`;
- stdout: `variable.persisted=True`.

## Assumptions

- The target variable already exists.
- The target variable is a text variable.
- The recipe writes only into `TFLEX_HARNESS_ARTIFACTS_DIR`.

## Limitations

- This recipe sets text variables only.
- It sets a constant expression and verifies via `TextValue` after reopen.
- Real variables and document properties are separate Phase 4 work.
