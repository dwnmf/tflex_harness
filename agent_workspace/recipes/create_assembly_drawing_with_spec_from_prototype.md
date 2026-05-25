# Recipe: create_assembly_drawing_with_spec_from_prototype

## Purpose

Create an assembly drawing with specification from the installed drawing prototype, set Title, save, reopen, and verify.

Phase 5 category recipe. Source remains visible C# and helper source set `easy_document_properties`.

## Documentation Evidence

Docs used:

- `D:\REALPROJECTS\tflex_api\llm\symbols.jsonl`
- Existing verified helper recipe `prototype_set_document_property`.

## C# Source

Snippet: `agent_workspace/recipes/create_assembly_drawing_with_spec_from_prototype.cs`

Default prototype: `Чертежи/Сборочный чертёж со спецификацией.grb`

Default target: `Title`

Default value: `Harness Assembly Drawing With Spec`

## Live Verification Report

Test: `create_assembly_drawing_with_spec_from_prototype`

Docs used:

- Existing verified helper recipe `prototype_set_document_property`.

Snippet: `agent_workspace/recipes/create_assembly_drawing_with_spec_from_prototype.cs`

Result: pass.

Evidence:

- live run directory: `artifacts/runs/20260525_214440_312277_recipe_create_assembly_drawing_with_spec_from_prototype`;
- command: `python -m tflex_harness.cli run-recipe create_assembly_drawing_with_spec_from_prototype --timeout-sec 120`;
- source prototype: `C:\Program Files\T-FLEX CAD 17\Program\Прототипы\Чертежи\Сборочный чертёж со спецификацией.grb`;
- category default property: `Title`;
- category default value: `Harness Assembly Drawing With Spec`;
- stdout: `document.opened=True`;
- stdout: `documentProperty.exists=True`;
- stdout: `documentProperty.after.Title=Harness Assembly Drawing With Spec`;
- stdout: `endChanges=OK`;
- stdout: `documentProperty.set=True`;
- stdout: `document.saved=True`;
- stdout: `document.outputSize=47462`;
- stdout: `documentProperty.reopened=Harness Assembly Drawing With Spec`;
- stdout: `documentProperty.persisted=True`;
- stdout: `easy.session=False`;
- run returned exit code `0`.

Blockers: none for this verified document-property path.

## Limitations

- This recipe edits a writable document property only.
- It does not yet expose deeper category-specific semantics.
