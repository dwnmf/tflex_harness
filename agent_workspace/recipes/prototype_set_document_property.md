# Recipe: prototype_set_document_property

## Purpose

Copy one installed T-FLEX `.grb` prototype into the run artifact directory, open the copy, set one writable string property on `Document.Properties`, save a new `.grb`, reopen it, and verify the property value persisted.

This is Phase 4 document-property mutation for prototype-driven document generation.

## Documentation Evidence

Docs used:

- `D:\REALPROJECTS\tflex_api\llm\symbols.jsonl`
- `T:TFlex.Model.DocumentProperties`
- `P:TFlex.Model.Document.Properties`
- `P:TFlex.Model.DocumentProperties.Author`
- `P:TFlex.Model.DocumentProperties.Title`
- `P:TFlex.Model.DocumentProperties.Subject`
- `P:TFlex.Model.DocumentProperties.Company`
- `P:TFlex.Model.DocumentProperties.Category`
- `P:TFlex.Model.DocumentProperties.Keywords`
- `M:TFlex.Model.Document.GetTextProperty(System.String)`.

## C# Source

Snippet: `agent_workspace/recipes/prototype_set_document_property.cs`

This recipe compiles with helper source set `easy_document_properties` from `src/tflex_harness/csharp_helpers`.

Input:

```text
TFLEX_PROTOTYPE_SOURCE_PATH=<absolute path to source .grb prototype>
TFLEX_DOCUMENT_PROPERTY_NAME=<writable string DocumentProperties property>
TFLEX_DOCUMENT_PROPERTY_TEXT=<new property text>
```

Harness recipe args:

```text
source_path=<absolute .grb path>
prototype_id=<catalog id, optional when source_path is provided>
prototype_selector=<catalog id/name/relative path alias, optional>
property_name=<writable string property name, e.g. Title or Author>
text_value=<new value>
```

## Live Verification Report

Test: `prototype_set_document_property`

Docs used:

- `D:\REALPROJECTS\tflex_api\llm\types\TFlexAPI__TFlex.Model.DocumentProperties__*.md`
- Live probe `artifacts/runs/20260525_181722_045147_document_properties_probe` to confirm `Title`, `Author`, `Subject`, `Company`, `Category`, and `Keywords` are writable strings.

Snippet: `agent_workspace/recipes/prototype_set_document_property.cs`

Result: pass.

Evidence:

- live run directory: `artifacts/runs/20260525_181851_320860_recipe_prototype_set_document_property`;
- command: `python -m tflex_harness.cli run-recipe prototype_set_document_property --arg 'prototype_id=2D Деталь' --arg 'property_name=Title' --arg 'text_value=Harness Document Property Test' --timeout-sec 120`;
- source prototype: `C:\Program Files\T-FLEX CAD 17\Program\Прототипы\2D Деталь.grb`;
- property: `Title`;
- stdout: `documentProperty.exists=True`;
- stdout: `documentProperty.before.Title=`;
- stdout: `documentProperty.after.Title=Harness Document Property Test`;
- stdout: `endChanges=OK`;
- stdout: `documentProperty.set=True`;
- stdout: `document.saved=True`;
- stdout: `documentProperty.reopened=Harness Document Property Test`;
- stdout: `documentProperty.persisted=True`;
- stdout: `easy.session=False`;
- run returned exit code `0`.

Blockers: none for the verified `Title` document property in `2D Деталь.grb`.

## Assumptions

- The target property exists on `Document.Properties`.
- The target property is a writable string property.
- The recipe writes only into `TFLEX_HARNESS_ARTIFACTS_DIR`.

## Limitations

- This recipe edits public writable string properties only.
- It does not edit date, GUID, unit, or numeric document properties.
- It does not edit variables; variable recipes are separate.
