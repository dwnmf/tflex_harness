# Recipe: prototype_set_real_variable

## Purpose

Copy one installed T-FLEX `.grb` prototype into the run artifact directory, open the copy, set one existing real-number variable to a constant value, save a new `.grb`, reopen it, and verify the variable value persisted.

This is the second Phase 4 mutation recipe for prototype-driven document generation.

## Documentation Evidence

Docs used:

- `D:\REALPROJECTS\tflex_api\llm\symbols.jsonl`
- `T:TFlex.Model.Variable` for variable objects.
- `M:TFlex.Model.Document.GetVariables` from existing live state/metadata probes.
- `P:TFlex.Model.Variable.Expression`, `P:TFlex.Model.Variable.RealValue`, `P:TFlex.Model.Variable.IsReal`.
- `M:TFlex.Model.Document.BeginChanges`, `M:TFlex.Model.Document.EndChanges`.
- `M:TFlex.Model.Document.SaveAs(System.String)`.

## C# Source

Snippet: `agent_workspace/recipes/prototype_set_real_variable.cs`

This recipe compiles with helper source set `easy_variables` from `src/tflex_harness/csharp_helpers`.

Input:

```text
TFLEX_PROTOTYPE_SOURCE_PATH=<absolute path to source .grb prototype>
TFLEX_VARIABLE_NAME=<existing real variable name>
TFLEX_VARIABLE_REAL_VALUE=<new invariant-culture number>
```

Harness recipe args:

```text
source_path=<absolute .grb path>
prototype_id=<catalog id, optional when source_path is provided>
prototype_selector=<catalog id/name/relative path alias, optional>
variable_name=<existing real variable name>
real_value=<new invariant-culture number>
```

## Live Verification Report

Test: `prototype_set_real_variable`

Docs used:

- `D:\REALPROJECTS\tflex_api\llm\types\TFlexAPI__TFlex.Model.Variable__*.md`
- Live metadata index `artifacts/prototype_metadata/live_all_20260525/metadata/001_2D.json` to choose `Nomer_Shem`.

Snippet: `agent_workspace/recipes/prototype_set_real_variable.cs`

Result: pass.

Evidence:

- live run directory: `artifacts/runs/20260525_180343_657081_recipe_prototype_set_real_variable`;
- command: `python -m tflex_harness.cli run-recipe prototype_set_real_variable --arg 'prototype_id=2D Деталь' --arg 'variable_name=Nomer_Shem' --arg 'real_value=42' --timeout-sec 120`;
- source prototype: `C:\Program Files\T-FLEX CAD 17\Program\Прототипы\2D Деталь.grb`;
- variable: `Nomer_Shem`;
- stdout: `variable.exists=True`;
- stdout: `variable.before.Nomer_Shem=0`;
- stdout: `variable.expression.Nomer_Shem=42`;
- stdout: `endChanges=OK`;
- stdout: `variable.set=True`;
- stdout: `document.saved=True`;
- stdout: `variable.reopened=42`;
- stdout: `variable.persisted=True`;
- stdout: `easy.session=False`;
- run returned exit code `0`.

Blockers: none for the verified `Nomer_Shem` real variable in `2D Деталь.grb`.

## Assumptions

- The target variable already exists.
- The target variable is a real-number variable.
- The recipe writes only into `TFLEX_HARNESS_ARTIFACTS_DIR`.

## Limitations

- This recipe sets real variables only.
- It sets a constant expression and verifies via `RealValue` after reopen.
- Text variables use `prototype_set_text_variable`.
