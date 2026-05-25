# T-FLEX Harness Goal

Date: 2026-05-25.

Scope: make `tflex_harness` able to create, inspect, fill, validate, and export T-FLEX documents from the installed prototype library:

```text
C:\Program Files\T-FLEX CAD 17\Program\Прототипы
```

This file is the active project plan. It replaces the old helper-only goal. Helpers stay, but the larger target is now a **prototype-driven document factory**.

## Mission

Use the official T-FLEX CAD 17 `.grb` prototypes as trusted seeds, and drive them through our harness with visible C# snippets, source helpers, live CAD runs, and evidence artifacts.

The harness should let an agent or user say:

> create this kind of T-FLEX document using this prototype, fill these fields/tables/model data, validate it, and export artifacts.

The system must work for the whole installed prototype set, not only gear/3D examples.

## Current Prototype Corpus

Observed source root:

```text
C:\Program Files\T-FLEX CAD 17\Program\Прототипы
```

Observed top-level content:

```text
2D Деталь.grb
2D Сборка.grb
3D Деталь.grb
3D Сборка.grb
Листовая Деталь.grb
Спецификации\
Таблицы\
Техкарты\
Фотореализм\
Фрагменты\
Чертежи\
Электротехника\
Library.ico
Order.txt
TemplateSettings.xml
```

Observed file counts:

```text
.grb  50
.ico   5
.txt   1
.xml   1
```

Observed prototype groups:

```text
Спецификации   21 files
Таблицы         7 files
Техкарты        2 files
Фотореализм     3 files
Фрагменты       3 files
Чертежи         5 files
Электротехника  8 files
root            5 GRB prototypes
```

Important rule: the source directory under `Program Files` is read-only input. Never modify prototypes in place.

## Definition Of Done

The harness can be called with:

- prototype selector: exact path, relative path, category/name, or catalog id;
- input payload: JSON/YAML with variables, title-block fields, table rows, metadata, model references, export targets;
- visible C# snippet or recipe name;
- helper set names;
- validation contract.

It produces:

- copied working `.grb`;
- modified output `.grb`;
- optional exports: STEP, PDF, image, DXF/DWG, neutral files when supported;
- stdout evidence;
- `request.json`;
- `result.json`;
- prototype hash evidence;
- helper source hash evidence;
- validation report;
- run directory under `artifacts/runs/...`.

## Core Architecture

Python remains orchestration.

C# remains CAD execution.

Helpers are C# source files compiled with visible snippets. They are not hidden DLL magic.

Canonical source helpers live here:

```text
src/tflex_harness/csharp_helpers/
```

Prototype and document automation should use this pattern:

```text
user payload
  -> Python catalog/runner
  -> visible C# snippet
  -> helper source files
  -> live T-FLEX CAD
  -> artifacts/runs/<timestamp>_<prefix>/
```

## Hard Invariants

- Do not edit `C:\Program Files\T-FLEX CAD 17\Program\Прототипы` in place.
- Always copy the selected `.grb` to the run artifact directory before modification.
- Preserve Cyrillic paths and names.
- Print evidence, not vibes.
- Every prototype run records:
  - original path;
  - copied path;
  - output path;
  - file size;
  - SHA256;
  - document type guess;
  - helper files and hashes;
  - export files and sizes.
- Every claim about T-FLEX API behavior needs compile/live evidence.
- Helpers may reduce boilerplate, but source must stay visible.
- If a prototype cannot be semantically modified yet, the harness must still open/copy/save/export it and report why semantic filling was skipped.

## Non-Goals

- No opaque Python CAD SDK replacing T-FLEX API.
- No silent mutation of installed templates.
- No broad “do everything” helper that hides real API calls.
- No fake success based only on file existence.
- No name-based reward hacking when geometry/table/document evidence is available.
- No long-lived T-FLEX session as default.

## Main Capabilities To Build

### 1. Prototype Catalog

Create a catalog module:

```text
src/tflex_harness/prototypes.py
```

Responsibilities:

- scan `C:\Program Files\T-FLEX CAD 17\Program\Прототипы`;
- support override root via env var `TFLEX_PROTOTYPES_DIR`;
- index all `.grb`, `.xml`, `.txt`, `.ico`;
- preserve relative paths;
- compute SHA256 and size;
- detect category from directory;
- generate stable ids;
- write catalog JSON under artifacts.

Planned CLI:

```powershell
python -m tflex_harness.cli prototypes-scan
python -m tflex_harness.cli prototypes-list
python -m tflex_harness.cli prototypes-info "Чертежи/Чертёж детали с форматкой"
```

Evidence:

- catalog count equals observed 50 `.grb`;
- paths with Cyrillic round-trip correctly;
- hashes are stable.

### 2. Prototype Open/Copy/Save Probe

Create a minimal live C# probe that:

- receives prototype path;
- copies it to run dir;
- opens copy in T-FLEX;
- prints document metadata;
- saves as output `.grb`;
- closes document cleanly.

This is the first required live milestone.

Planned helper:

```text
src/tflex_harness/csharp_helpers/TFlexEasyPrototype.cs
```

Initial API:

```csharp
namespace TFlexEasy {
  public static class EasyPrototype {
    public static string CopyToArtifact(string sourcePath, string artifactPath);
    public static TFlex.Model.Document OpenCopy(string copiedPath, bool visible);
    public static bool SaveAsGrb(TFlex.Model.Document doc, string outputPath);
    public static void PrintPrototypeEvidence(string label, string sourcePath, string copiedPath, string outputPath);
  }
}
```

Validation:

- compile-only;
- live run against one root prototype;
- live batch against all 50 `.grb` prototypes in open/copy/save mode.

### 3. Document Metadata Probe

Create a read-only C# probe for any opened prototype:

- document name;
- document path;
- page count if available;
- 2D/3D operation counts if available;
- variables;
- text objects if available;
- table-like objects if available;
- fragments/references if available;
- document parameters/properties if available.

Output format:

```text
prototype.id=...
document.opened=True
document.pages=...
document.variables.count=...
document.operations3d.count=...
document.text.count=...
document.tables.count=...
```

Artifacts:

```text
artifacts/prototype_catalog/<date>/metadata/<prototype-id>.json
artifacts/runs/<run>/stdout.txt
```

Purpose:

- classify prototypes by actual API-visible content, not by filename only;
- discover which document types need which helpers.

### 4. Document Mutation Helpers

Add narrow source helpers only after probes prove API behavior.

Planned helper files:

```text
src/tflex_harness/csharp_helpers/TFlexEasyDocuments.cs
src/tflex_harness/csharp_helpers/TFlexEasyVariables.cs
src/tflex_harness/csharp_helpers/TFlexEasyText.cs
src/tflex_harness/csharp_helpers/TFlexEasyTables.cs
src/tflex_harness/csharp_helpers/TFlexEasyDrawings.cs
src/tflex_harness/csharp_helpers/TFlexEasySpecs.cs
src/tflex_harness/csharp_helpers/TFlexEasyElectrical.cs
```

Rules:

- each helper does one small class of mutation;
- each helper prints what it changed;
- each helper can run in dry-run mode;
- each helper has compile test;
- each helper has at least one live prototype test.

Initial desired APIs:

```csharp
EasyVariables.Set(doc, "Designation", "ABC.001");
EasyVariables.SetIfExists(doc, "Material", "Steel 20");
EasyText.ReplaceAll(doc, "{{DESIGNATION}}", "ABC.001");
EasyTables.SetCell(doc, tableSelector, row, column, value);
EasyDocuments.SetProperty(doc, "Author", "tflex_harness");
EasyDocuments.PrintSummary(doc);
```

No helper is accepted without evidence.

### 5. Payload Contract

Standard input payload for document generation:

```json
{
  "prototype": {
    "id": "drawings/detail-format",
    "path": null
  },
  "output": {
    "name": "ABC.001_detail",
    "exports": ["grb", "pdf"]
  },
  "document": {
    "properties": {
      "Author": "tflex_harness"
    },
    "variables": {
      "Designation": "ABC.001",
      "Name": "Корпус",
      "Material": "Сталь 20"
    },
    "text_replacements": {
      "{{DESIGNATION}}": "ABC.001",
      "{{NAME}}": "Корпус"
    },
    "tables": []
  },
  "validation": {
    "require_open": true,
    "require_save": true,
    "require_exports": ["grb"]
  }
}
```

Payload lives in run dir as `input_payload.json`.

### 6. Document Recipe System

A document recipe is:

- prototype id;
- input payload schema;
- visible C# snippet;
- helper set;
- validation expectations;
- last live evidence.

Recipe examples:

```text
agent_workspace/recipes/prototype_open_copy_save/
agent_workspace/recipes/create_3d_part_from_prototype/
agent_workspace/recipes/create_3d_assembly_from_prototype/
agent_workspace/recipes/create_detail_drawing_from_prototype/
agent_workspace/recipes/create_assembly_drawing_with_spec/
agent_workspace/recipes/create_gost_specification/
agent_workspace/recipes/create_parameter_table/
agent_workspace/recipes/create_electrical_scheme/
```

Each recipe must be runnable by harness and must state limitations.

### 7. Batch Validation Matrix

Build a prototype validation matrix.

Columns:

- prototype id;
- path;
- category;
- hash;
- opens;
- saves copy;
- exports GRB;
- exports PDF if 2D/document;
- exports STEP if 3D/model;
- metadata extracted;
- variables writable;
- text writable;
- tables writable;
- known limitations;
- last run dir.

Expected first target:

```text
50 / 50 prototypes open from copied path
50 / 50 prototypes save as GRB copy
0 source prototypes modified
```

Semantic mutation can come later per category.

### 8. Export Layer

Current helper exists:

```text
TFlexEasyExport.cs
```

Extend carefully with evidence:

```csharp
EasyExport.Grb(doc, path);
EasyExport.Step(doc, path);
EasyExport.Pdf(doc, path);
EasyExport.Image(doc, path);
EasyExport.Dxf(doc, path);
EasyExport.Dwg(doc, path);
```

Rules:

- every export method checks file exists;
- every export method prints file size;
- unsupported export returns false with diagnostic reason;
- no export method overwrites outside artifact dir unless explicitly allowed.

### 9. Category-Specific Tracks

#### Root 3D/2D Prototypes

Targets:

- `2D Деталь.grb`
- `2D Сборка.grb`
- `3D Деталь.grb`
- `3D Сборка.grb`
- `Листовая Деталь.grb`

Capabilities:

- open/copy/save;
- set variables/properties;
- create simple geometry or insert generated model;
- export GRB;
- export STEP for 3D;
- export PDF/image for 2D when supported.

#### Drawings

Group:

```text
Чертежи\
```

Targets:

- detail drawing with format;
- assembly drawing with format;
- assembly drawing with specification;
- text document with format.

Capabilities:

- fill title block;
- set designation/name/material;
- update sheet metadata;
- insert or reference model if API allows;
- export PDF;
- validate page count and visible text.

#### Specifications

Group:

```text
Спецификации\
```

Capabilities:

- fill rows from payload;
- preserve GOST form layout;
- print row/column evidence;
- export GRB/PDF;
- validate required columns.

#### Tables

Group:

```text
Таблицы\
```

Capabilities:

- fill parameter table rows;
- fill gear parameter table;
- fill chain parameter table;
- fill weld table;
- validate row count and non-empty cells.

#### Tech Cards

Group:

```text
Техкарты\
```

Capabilities:

- fill operation/process fields;
- export PDF;
- validate required operation rows.

#### Fragments

Group:

```text
Фрагменты\
```

Capabilities:

- open/save fragment prototypes;
- create fragment outputs;
- use fragment outputs in assemblies later;
- preserve fragment LCS evidence.

#### Electrical

Group:

```text
Электротехника\
```

Capabilities:

- open/copy/save all electrical prototypes;
- inspect symbols/components/tables if API-visible;
- fill component properties where API permits;
- export PDF/GRB;
- document unsupported API gaps explicitly.

#### Photorealism

Group:

```text
Фотореализм\
```

Capabilities:

- open/copy/save;
- inspect scene/camera/light objects if API-visible;
- render/export image only after live API proof.

## Implementation Phases

### Phase 0: Preserve Current Work

Status: pending.

Tasks:

- keep existing helper/gears/GRB reverse work intact;
- do not regress `run-csharp --helper`;
- do not regress `reverse-evidence`;
- do not commit generated heavy artifacts unless explicitly requested.

Validation:

```powershell
python -m pytest tests/unit/test_grb_reverse.py tests/smoke/test_cli.py -v
```

### Phase 1: Catalog Installed Prototypes

Status: implemented.

Tasks:

- implement `src/tflex_harness/prototypes.py`;
- add CLI scan/list/info;
- add tests with a temp fake prototype tree;
- scan real installed tree.

Validation:

```powershell
python -m pytest tests/unit/test_prototypes.py tests/smoke/test_cli.py -v
python -m tflex_harness.cli prototypes-scan
```

Evidence:

- `tests/unit/test_prototypes.py` and `tests/smoke/test_cli.py` passed;
- real catalog JSON: `artifacts/prototype_catalog/current_probe/catalog.json`;
- real scan: `file_count=57`, `grb_count=50`;
- Cyrillic paths preserved.

### Phase 2: Open/Copy/Save All Prototypes

Status: implemented.

Tasks:

- implement `TFlexEasyPrototype.cs`;
- implement one visible C# probe;
- add runner helper set `easy_prototype`;
- add verified recipe `prototype_open_copy_save`;
- run one prototype live;
- batch-run all 50 `.grb`;
- write JSON/CSV validation matrix.

Validation:

```powershell
python -m tflex_harness.cli run-csharp --mode compile_only --helper easy_prototype --code "<probe>"
python scripts/prototype_batch_open_save.py
```

Evidence:

- one-prototype live run passed: `artifacts/runs/20260525_172319_936833_prototype_open_copy_save_3d_part`;
- source SHA equals copy SHA for `3D Деталь.grb`;
- output `.grb` size non-zero;
- full live batch matrix: `artifacts/prototype_validation/live_all_20260525/prototype_open_save_matrix.json`;
- full live batch CSV: `artifacts/prototype_validation/live_all_20260525/prototype_open_save_matrix.csv`;
- live batch summary: `selected=50`, `attempted=50`, `passed=50`, `failed=0`.

### Phase 3: Metadata Extraction

Status: implemented.

Tasks:

- create metadata probe;
- inspect API docs for document/page/text/table/variable access;
- extract common fields;
- write JSON per prototype;
- write metadata index JSON/CSV.

Validation:

- one root 3D prototype;
- one drawing prototype;
- one specification prototype;
- one electrical prototype;
- then full batch.

Evidence:

- CLI command: `python -m tflex_harness.cli prototypes-metadata`;
- one-prototype live probe passed: `artifacts/prototype_metadata/live_one_20260525_fix/prototype_metadata_index.json`;
- full live metadata batch: `artifacts/prototype_metadata/live_all_20260525/prototype_metadata_index.json`;
- full live metadata CSV: `artifacts/prototype_metadata/live_all_20260525/prototype_metadata_index.csv`;
- per-prototype JSON dir: `artifacts/prototype_metadata/live_all_20260525/metadata`;
- live metadata summary: `selected=50`, `attempted=50`, `passed=50`, `failed=0`;
- extracted fields include 2D object counts, text-like 2D counts, table-like heuristic counts, 3D operation counts, variable counts, reflected page counts, reflected fragment counts, type histograms, variable records, and errors.

### Phase 4: Minimal Mutation

Status: started.

Tasks:

- implement text variable setting helper;
- implement document property helper;
- implement text replacement helper if API-visible;
- prove on one drawing/spec/table prototype.

Validation:

- stdout says before/after;
- reopen output and verify persisted value;
- export PDF when supported.

Current evidence:

- C# helper source: `src/tflex_harness/csharp_helpers/TFlexEasyVariables.cs`;
- helper set: `easy_variables`;
- helper set: `easy_text`;
- helper set: `easy_document_properties`;
- recipe: `prototype_set_text_variable`;
- recipe: `prototype_set_real_variable`;
- recipe: `prototype_set_table_cell`;
- recipe: `prototype_set_document_property`;
- recipe: `prototype_replace_visible_text`;
- live command: `python -m tflex_harness.cli run-recipe prototype_set_text_variable --arg 'prototype_id=2D Деталь' --arg 'variable_name=$Наименование' --arg 'text_value=Harness Recipe Test' --timeout-sec 120`;
- live run: `artifacts/runs/20260525_175508_317973_recipe_prototype_set_text_variable`;
- verified stdout: `variable.exists=True`, `variable.set=True`, `document.saved=True`, `variable.reopened=Harness Recipe Test`, `variable.persisted=True`;
- live command: `python -m tflex_harness.cli run-recipe prototype_set_real_variable --arg 'prototype_id=2D Деталь' --arg 'variable_name=Nomer_Shem' --arg 'real_value=42' --timeout-sec 120`;
- live run: `artifacts/runs/20260525_180343_657081_recipe_prototype_set_real_variable`;
- verified stdout: `variable.exists=True`, `variable.expression.Nomer_Shem=42`, `variable.set=True`, `document.saved=True`, `variable.reopened=42`, `variable.persisted=True`;
- live command: `python -m tflex_harness.cli run-recipe prototype_set_table_cell --arg 'prototype_id=Таблицы/Таблица параметров зубчатого колеса.grb' --arg 'cell_index=2' --arg 'text_value=Harness Table Test' --timeout-sec 120`;
- live run: `artifacts/runs/20260525_181242_346840_recipe_prototype_set_table_cell`;
- verified stdout: `richText.count=1`, `table.cell.after=Harness Table Test`, `table.cell.set=True`, `document.saved=True`, `table.cell.reopened=Harness Table Test`, `table.cell.persisted=True`;
- live command: `python -m tflex_harness.cli run-recipe prototype_set_document_property --arg 'prototype_id=2D Деталь' --arg 'property_name=Title' --arg 'text_value=Harness Document Property Test' --timeout-sec 120`;
- live run: `artifacts/runs/20260525_181851_320860_recipe_prototype_set_document_property`;
- verified stdout: `documentProperty.exists=True`, `documentProperty.after.Title=Harness Document Property Test`, `documentProperty.set=True`, `document.saved=True`, `documentProperty.reopened=Harness Document Property Test`, `documentProperty.persisted=True`;
- live command: `python -m tflex_harness.cli run-recipe prototype_replace_visible_text --arg 'prototype_id=Электротехника/Клеммник.grb' --arg 'search_text=Цепь' --arg 'replacement_text=Harness Circuit' --timeout-sec 120`;
- live run: `artifacts/runs/20260525_182531_611149_recipe_prototype_replace_visible_text`;
- verified stdout: `visibleText.beforeCount=1`, `visibleText.line.after=Harness Circuit`, `visibleText.replaceCount=1`, `document.saved=True`, `visibleText.oldAfter=0`, `visibleText.newAfter=1`, `visibleText.persisted=True`;
- source prototype: `C:\Program Files\T-FLEX CAD 17\Program\Прототипы\2D Деталь.grb`;
- saved copies: `artifacts/variable_mutation_copy.grb`, `artifacts/variable_mutation_saved.grb`.

Remaining Phase 4 work:

- category coverage beyond `2D Деталь.grb`.

### Phase 5: Category Recipes

Status: started.

Tasks:

- create one recipe per category;
- give each recipe a payload schema;
- record live evidence;
- document limitations.

Validation:

- recipe registry lists all category recipes;
- each recipe has at least one live run.

Current Phase 5 evidence:

- recipe: `create_detail_drawing_from_prototype`;
- recipe: `create_specification_from_prototype`;
- helper set: `easy_document_properties`;
- live drawing command: `python -m tflex_harness.cli run-recipe create_detail_drawing_from_prototype --timeout-sec 120`;
- live drawing run: `artifacts/runs/20260525_212201_368610_recipe_create_detail_drawing_from_prototype`;
- live drawing evidence: `documentProperty.after.Title=Harness Detail Drawing`, `document.saved=True`, `document.outputSize=25462`, `documentProperty.persisted=True`;
- live specification command: `python -m tflex_harness.cli run-recipe create_specification_from_prototype --timeout-sec 120`;
- live specification run: `artifacts/runs/20260525_212204_093117_recipe_create_specification_from_prototype`;
- live specification evidence: `documentProperty.after.Title=Harness Specification`, `document.saved=True`, `document.outputSize=29138`, `documentProperty.persisted=True`.

Remaining Phase 5 work:

- category recipes for table documents, fragments, electrical docs, and 3D/assembly categories;
- richer category-specific payload fields beyond writable document properties.

### Phase 6: Batch Document Factory

Status: started.

Tasks:

- add CLI command that takes payload and prototype id;
- chooses recipe/helper set;
- runs live T-FLEX;
- emits output GRB and requested exports.

Planned CLI:

```powershell
python -m tflex_harness.cli create-document --payload input.json
```

Validation:

- create 3D part from prototype;
- create drawing from prototype;
- create specification from prototype;
- create table document from prototype.

Current Phase 6 evidence:

- module: `src/tflex_harness/document_factory.py`;
- CLI: `python -m tflex_harness.cli create-document --payload input.json`;
- sample matrix CLI: `python -m tflex_harness.cli document-factory-samples`;
- batch payload folder CLI: `python -m tflex_harness.cli document-factory-batch --payload-dir payloads`;
- dry-run support writes `input_payload.json` and `factory_plan.json` under a factory run directory;
- batch dry-run/live support writes `document_factory_batch_matrix.json`, `.csv`, and `document_factory_failure_report.json`;
- dispatcher executes generated visible C# when a payload has multiple supported mutation operations;
- single-operation payloads still dispatch to one verified recipe;
- supported dispatch groups: explicit `recipe`, `document.properties`, `document.variables`, `document.text_replacements`, `document.tables`, fallback `prototype_open_copy_save`;
- multi-step runs apply supported operations to one copied `.grb`, save once, reopen, and validate all mutations;
- output contract now accepts `output.name` and `output.exports`;
- supported output formats: `grb`, `step`, `pdf`, `dxf`, `dwg`;
- named GRB output is copied into the factory run as `artifacts/outputs/<sanitized-name>.grb`;
- named STEP output is exported from the saved `.grb` through a separate visible C# run and recorded as `artifacts/outputs/<sanitized-name>.step`;
- named PDF output is exported from the saved `.grb` through a separate visible C# run and recorded as `artifacts/outputs/<sanitized-name>.pdf`;
- named DXF/DWG output is exported from the saved `.grb` through separate visible C# runs and recorded as `artifacts/outputs/<sanitized-name>.dxf` / `.dwg`;
- unsupported formats are rejected at plan time instead of being silently skipped.
- live command: `python -m tflex_harness.cli create-document --payload artifacts/factory_payloads/phase6_property_payload.json --timeout-sec 120`;
- live factory run: `artifacts/runs/20260525_183154_667605_document_factory`;
- live recipe run: `artifacts/runs/20260525_183154_769543_recipe_prototype_set_document_property`;
- selected recipe: `prototype_set_document_property`;
- verified stdout: `documentProperty.after.Title=Harness Factory Live Test`, `document.saved=True`, `documentProperty.reopened=Harness Factory Live Test`, `documentProperty.persisted=True`.
- live named GRB command: `python -m tflex_harness.cli create-document --payload artifacts/factory_payloads/phase6_named_grb_payload.json --timeout-sec 120`;
- live named GRB factory run: `artifacts/runs/20260525_184829_962489_document_factory`;
- live named GRB recipe run: `artifacts/runs/20260525_184830_053534_recipe_prototype_set_document_property`;
- live named GRB output: `artifacts/runs/20260525_184829_962489_document_factory/artifacts/outputs/phase6_named_output.grb`;
- live named GRB evidence: `outputs[0].format=grb`, `outputs[0].relative_path=artifacts/outputs/phase6_named_output.grb`, `outputs[0].size=23240`, `output_errors=[]`.
- live prototype STEP command: `python -m tflex_harness.cli create-document --payload artifacts/factory_payloads/phase6_3d_step_payload.json --timeout-sec 120`;
- live prototype STEP factory run: `artifacts/runs/20260525_190649_137237_document_factory`;
- live prototype STEP export run: `artifacts/runs/20260525_190650_981262_factory_step_export`;
- live prototype STEP output: `artifacts/runs/20260525_190649_137237_document_factory/artifacts/outputs/phase6_3d_step_export.step`, size `322`;
- live solid STEP command: `python -m tflex_harness.cli create-document --payload artifacts/factory_payloads/phase6_solid_step_payload.json --timeout-sec 120`;
- live solid STEP factory run: `artifacts/runs/20260525_190913_994364_document_factory`;
- live solid STEP export run: `artifacts/runs/20260525_190915_851463_factory_step_export`;
- live solid STEP output: `artifacts/runs/20260525_190913_994364_document_factory/artifacts/outputs/phase6_solid_step_export.step`, size `6919`;
- live solid STEP content evidence: `MANIFOLD_SOLID_BREP`, `CLOSED_SHELL`, `ADVANCED_FACE`;
- STEP runtime note: `ExportToSTEP.Export(...)` can print `easy.stepExportResult=False` while writing a valid non-empty STEP, so helper success is file-existence/size based.
- live PDF command: `python -m tflex_harness.cli create-document --payload artifacts/factory_payloads/phase6_drawing_pdf_payload.json --timeout-sec 120`;
- live PDF factory run: `artifacts/runs/20260525_192244_448383_document_factory`;
- live PDF recipe run: `artifacts/runs/20260525_192244_524243_recipe_prototype_set_document_property`;
- live PDF export run: `artifacts/runs/20260525_192245_937700_factory_pdf_export`;
- live PDF output: `artifacts/runs/20260525_192244_448383_document_factory/artifacts/outputs/phase6_drawing_pdf_export.pdf`, size `11109`;
- live PDF header evidence: `%PDF-1.5`;
- live PDF stdout evidence: `easy.pdfModuleSource=C:\Program Files\T-FLEX CAD 17\Program\PDFExport.dll`, `easy.pdfModuleLocalExists=True`, `easy.pdfExportResult=True`, `easy.pdfSaved=True`, `factory.pdfExport.saved=True`;
- PDF runtime note: `ExportToPDF` must be constructed with `new ExportToPDF(document)`; `Document.ExportToPDF` is not present in T-FLEX CAD 17. Live evidence also showed `PDFExport.dll` must be copied from the T-FLEX program directory to the snippet cwd before export.
- live DXF/DWG command: `python -m tflex_harness.cli create-document --payload artifacts/factory_payloads/phase6_drawing_acad_payload.json --timeout-sec 120`;
- live DXF/DWG factory run: `artifacts/runs/20260525_193001_690605_document_factory`;
- live DXF export run: `artifacts/runs/20260525_193003_794702_factory_dxf_export`;
- live DWG export run: `artifacts/runs/20260525_193005_958846_factory_dwg_export`;
- live DXF output: `artifacts/runs/20260525_193001_690605_document_factory/artifacts/outputs/phase6_drawing_acad_export.dxf`, size `125193`;
- live DWG output: `artifacts/runs/20260525_193001_690605_document_factory/artifacts/outputs/phase6_drawing_acad_export.dwg`, size `18220`;
- DXF/DWG header evidence: DXF contains `SECTION`, `$ACADVER`, `AC1027`; DWG starts with bytes `41 43 31 30 32 37` (`AC1027`);
- DXF/DWG stdout evidence: `easy.dxfExportResult=True`, `easy.dxfSaved=True`, `factory.dxfExport.saved=True`, `easy.dwgExportResult=True`, `easy.dwgSaved=True`, `factory.dwgExport.saved=True`;
- ACAD runtime note: `EasyExport.Dxf` wraps `Document.ExportToDXF.Export(path)` and `EasyExport.Dwg` wraps `Document.ExportToDWG.Export(path)`.
- live multi-step command: `python -m tflex_harness.cli create-document --payload artifacts/factory_payloads/phase6_multi_step_payload.json --timeout-sec 120`;
- live multi-step factory run: `artifacts/runs/20260525_183813_757471_document_factory`;
- generated snippet: `artifacts/runs/20260525_183813_757471_document_factory/factory_snippet.cs`;
- live multi-step snippet run: `artifacts/runs/20260525_183813_840239_factory_multi_step`;
- verified stdout: `documentProperty.after.Title=Harness Multi Step Test`, `visibleText.line.after=Harness Circuit Multi`, `factory.allSet=True`, `document.saved=True`, `factory.property.0=Harness Multi Step Test`, `factory.visibleText.oldAfter.1=0`, `factory.visibleText.newAfter.1=1`, `factory.allValid=True`.
- live sample matrix command: `python -m tflex_harness.cli document-factory-samples --timeout-sec 120 --output-dir artifacts/document_factory_validation/live_samples_20260525_fix`;
- live sample matrix: `artifacts/document_factory_validation/live_samples_20260525_fix/document_factory_samples_matrix.json`;
- live sample matrix csv: `artifacts/document_factory_validation/live_samples_20260525_fix/document_factory_samples_matrix.csv`;
- live sample matrix summary: `selected=4`, `attempted=4`, `passed=4`, `failed=0`;
- live sample matrix categories: `3d_part`, `drawing`, `specification`, `table`;
- live sample matrix outputs: `factory_3d_part.grb` size `28542`, `factory_drawing.grb` size `25465`, `factory_specification.grb` size `29101`, `factory_table.grb` size `63297`.
- live sample matrix with STEP command: `python -m tflex_harness.cli document-factory-samples --timeout-sec 120 --output-dir artifacts/document_factory_validation/live_samples_step_20260525`;
- live sample matrix with STEP: `artifacts/document_factory_validation/live_samples_step_20260525/document_factory_samples_matrix.json`;
- live sample matrix with STEP summary: `selected=4`, `attempted=4`, `passed=4`, `failed=0`;
- live sample matrix with STEP 3D row: `output_formats=["grb","step"]`, `step_output_size=316`.
- live sample matrix with PDF command: `python -m tflex_harness.cli document-factory-samples --timeout-sec 120 --output-dir artifacts/document_factory_validation/live_samples_pdf_20260525`;
- live sample matrix with PDF: `artifacts/document_factory_validation/live_samples_pdf_20260525/document_factory_samples_matrix.json`;
- live sample matrix with PDF summary: `selected=4`, `attempted=4`, `passed=4`, `failed=0`;
- live sample matrix with PDF drawing row: `output_formats=["grb","pdf"]`, `pdf_output_size=11109`.
- live sample matrix with PDF+DXF+DWG command: `python -m tflex_harness.cli document-factory-samples --timeout-sec 120 --output-dir artifacts/document_factory_validation/live_samples_acad_20260525`;
- live sample matrix with PDF+DXF+DWG: `artifacts/document_factory_validation/live_samples_acad_20260525/document_factory_samples_matrix.json`;
- live sample matrix with PDF+DXF+DWG csv: `artifacts/document_factory_validation/live_samples_acad_20260525/document_factory_samples_matrix.csv`;
- live sample matrix with PDF+DXF+DWG summary: `selected=4`, `attempted=4`, `passed=4`, `failed=0`;
- live sample matrix with PDF+DXF+DWG drawing row: `output_formats=["grb","pdf","dxf","dwg"]`, `pdf_output_size=11109`, `dxf_output_size=125189`, `dwg_output_size=18220`.

Remaining Phase 6 work:

- polish output error classification around all supported formats.

### Phase 7: Enterprise Workflow

Status: started.

Tasks:

- support batch payload folder; **implemented initial CLI**
- support per-run summary CSV/JSON; **implemented initial batch matrix**
- support failure classification; **implemented initial buckets**
- support dry-run; **implemented**
- support “open only” audit mode; **implemented initial `--audit-open-only`**
- support rerun failed prototypes only; **implemented initial `--failed-matrix`**

Validation:

- batch report with success/fail/unsupported buckets;
- no silent failures.

Current Phase 7 evidence:

- module: `src/tflex_harness/document_factory_batch.py`;
- CLI: `python -m tflex_harness.cli document-factory-batch --payload-dir payloads`;
- rerun failed CLI: `python -m tflex_harness.cli document-factory-batch --failed-matrix document_factory_batch_matrix.json`;
- open-only audit CLI: `python -m tflex_harness.cli document-factory-batch --payload-dir payloads --audit-open-only`;
- MCP tools: `create_tflex_document`, `run_tflex_document_factory_batch`;
- supports `--glob`, `--recursive`, `--timeout-sec`, `--dry-run`, `--fail-fast`, `--failed-matrix`, `--audit-open-only`, and `--output-dir`;
- output files: `document_factory_batch_matrix.json`, `document_factory_batch_matrix.csv`, `document_factory_failure_report.json`;
- row evidence includes payload path/name, status, `failure_kind`, stage, recipe, selection, first output, STEP/PDF/DXF/DWG output paths/sizes, factory run dir, audit run dir, metadata counts, and error;
- summary buckets include `passed`, `input_failed`, `timeout_failed`, `export_failed`, `recipe_failed`, `run_failed`, and `unknown_failed`.
- failure report evidence includes `failed_count`, `failed_payloads`, `failed_by_kind`, and `rerun_failed_hint`.
- live open-only audit command: `python -m tflex_harness.cli document-factory-batch --payload-dir artifacts/factory_payloads --glob phase6_property_payload.json --audit-open-only --timeout-sec 120 --output-dir artifacts/document_factory_batches/live_audit_open_only_20260525`;
- live open-only audit matrix: `artifacts/document_factory_batches/live_audit_open_only_20260525/document_factory_batch_matrix.json`;
- live open-only audit summary: `selected=1`, `attempted=1`, `passed=1`, `failed=0`;
- live open-only audit run: `artifacts/runs/20260525_195835_783892_prototype_metadata`;
- live open-only row evidence: `stage=audit`, `audit_open_only=True`, `output_formats=[]`, `variables=47`, `pages=1`.

## Helper Set Plan

Existing useful helper sets stay:

```text
easy_core
easy_session
easy_3d
easy_gears
easy_export
all
```

Add new sets:

```text
easy_prototype
easy_documents
easy_tables
easy_drawings
easy_specs
easy_electrical
```

`all` must include them only after they compile cleanly.

## Evidence Schema

Every prototype/document run should print stable keys:

```text
prototype.sourcePath=...
prototype.sourceSha256=...
prototype.copyPath=...
prototype.copySize=...
document.opened=True
document.saved=True
document.outputPath=...
document.outputSize=...
export.pdf.path=...
export.pdf.size=...
validation.failures=0
```

`result.json` should include structured equivalents.

## Safety Rules

- Default output directory is artifact run dir.
- Writing outside artifacts requires explicit user path.
- Program Files prototype tree is never a write target.
- Batch jobs must have timeout per prototype.
- Failed prototype does not stop full batch unless `--fail-fast`.
- All failures include stdout/stderr/result path.

## Test Plan

Unit:

- catalog path handling;
- Cyrillic relative ids;
- SHA256;
- payload parsing;
- CLI argument validation.

Smoke:

- `prototypes-scan`;
- compile `easy_prototype`;
- fake payload to dry-run.

Integration/live:

- open/copy/save one prototype;
- batch open/copy/save all prototypes;
- mutate one variable/text/table where supported;
- export real outputs.

## Immediate Next Work

1. Analyze metadata JSON to choose mutation targets.
2. Implement variable setting helper.
3. Prove variable mutation on one copied prototype.
4. Implement document property helper if API-visible.
5. Add text/table helpers only after API proof.
6. Create category recipes for drawings, specifications, tables, fragments, electrical docs.

## Current Risks

- T-FLEX document APIs for tables/specifications/electrical objects may differ by document type.
- Some prototypes may require UI/interactive state to fully initialize.
- Export APIs may vary by document type.
- Cyrillic paths can expose encoding bugs.
- Some `.grb` prototypes may be protected or depend on environment files.

Mitigation:

- start with open/copy/save;
- probe metadata before mutation;
- write narrow helpers only after live evidence;
- keep unsupported states explicit.

## Plan Iteration Log

- 2026-05-25: Rewrote `goal.md` from helper-only target into prototype-driven document factory plan. Target source root: `C:\Program Files\T-FLEX CAD 17\Program\Прототипы`. Observed 50 `.grb` prototypes across root, specifications, tables, tech cards, photorealism, fragments, drawings, and electrical groups.
- 2026-05-25: Implemented Phase 1 prototype catalog. Added `src/tflex_harness/prototypes.py`, CLI commands `prototypes-scan`, `prototypes-list`, `prototypes-info`, unit/smoke tests, and real installed corpus scan evidence: `file_count=57`, `grb_count=50`, catalog at `artifacts/prototype_catalog/current_probe/catalog.json`.
- 2026-05-25: Started Phase 2. Added `TFlexEasyPrototype.cs`, helper set `easy_prototype`, recipe `prototype_open_copy_save`, and live proof for `C:\Program Files\T-FLEX CAD 17\Program\Прототипы\3D Деталь.grb`: run `artifacts/runs/20260525_172319_936833_prototype_open_copy_save_3d_part`, `document.opened=True`, `document.saved=True`, `document.closed=True`, output size `28544`.
- 2026-05-25: Completed Phase 2 baseline. Added `src/tflex_harness/prototype_validation.py` and CLI `prototypes-open-save-batch`. Live batch opened, saved, and closed all 50 installed `.grb` prototypes from artifact copies with `passed=50`, `failed=0`. Matrix: `artifacts/prototype_validation/live_all_20260525/prototype_open_save_matrix.json`.
- 2026-05-25: Completed Phase 3 baseline. Added `src/tflex_harness/prototype_metadata.py` and CLI `prototypes-metadata`. Live batch extracted metadata for all 50 installed `.grb` prototypes from artifact copies with `passed=50`, `failed=0`. Index: `artifacts/prototype_metadata/live_all_20260525/prototype_metadata_index.json`.
- 2026-05-25: Extended Phase 6 document factory output contract. Payloads can request `output.name` with `exports: ["grb"]`; factory materializes a named `.grb` under the factory run `artifacts/outputs/` and rejects unsupported export formats explicitly.
- 2026-05-25: Added `document-factory-samples` CLI and live sample matrix for 3D part, drawing, specification, and table prototype payloads. Live matrix passed `4/4` and produced named GRB outputs for all samples.
- 2026-05-25: Added STEP output materialization to document factory. STEP export runs as separate visible C# using `EasyPrototype.OpenCopy` and `EasyExport.Step`; live solid proof produced `phase6_solid_step_export.step` size `6919` containing `MANIFOLD_SOLID_BREP`, `CLOSED_SHELL`, and `ADVANCED_FACE`.
- 2026-05-25: Added PDF output materialization to document factory. PDF export runs as separate visible C# using `new ExportToPDF(document)` and `EasyExport.Pdf`; helper copies `PDFExport.dll` locally before export. Live drawing proof produced `phase6_drawing_pdf_export.pdf` size `11109` with `%PDF-1.5` header.
- 2026-05-25: Added DXF/DWG output materialization to document factory. ACAD exports run as separate visible C# using `Document.ExportToDXF.Export(path)` and `Document.ExportToDWG.Export(path)`. Live drawing proof produced DXF size `125193` with `AC1027` header evidence and DWG size `18220` with `AC1027` binary header.
- 2026-05-25: Started Phase 7 enterprise workflow with `document-factory-batch`. It runs all payload JSON files from a folder, supports dry-run/fail-fast/recursive globbing, and writes JSON/CSV batch matrices.
- 2026-05-25: Extended `document-factory-batch` with failure buckets and rerun-failed flow. Rows now include `failure_kind`; summaries include stable pass/fail buckets; `--failed-matrix` reruns only failed payload rows from a previous matrix.
- 2026-05-25: Added `--audit-open-only` to `document-factory-batch`. It resolves each payload prototype, runs the verified metadata open probe, records object/page/variable counts and audit run dir, and skips all mutation/save/export paths.
- 2026-05-25: Added `document_factory_failure_report.json` to batch runs. It is a compact machine-readable failure report grouped by `failure_kind`, with failed payload paths and rerun hint.
- 2026-05-25: Exposed document factory over MCP. Added `create_tflex_document` and `run_tflex_document_factory_batch` tools with smoke coverage for dry-run single payload and batch payload execution.
