# tflex_harness

Private T-FLEX CAD 17 harness/MCP workspace.

This project follows `goal.md`: Python is the thin control plane for MCP, documentation search, diagnostics, artifacts, and process execution; C# is used for typed snippets against the real T-FLEX CAD 17 .NET API.

## Quick checks

```powershell
python -m pytest tests/unit -v
python -m pytest tests/smoke -v
python -m tflex_harness.cli env
python -m tflex_harness.cli search "TFlex.Model.Document" --limit 5
python -m tflex_harness.cli run-csharp --code "public class Program { public static int Main(){ System.Console.WriteLine(\"ok\"); return 0; } }"
python -m tflex_harness.cli recipes
python -m tflex_harness.cli state
# after `pip install -e .[mcp]`
tflex-harness-mcp
```

Live T-FLEX integration checks are marked `integration` and may skip when the CAD runtime is unavailable.

## Implemented tools

- `search_tflex_docs` / `python -m tflex_harness.cli search` — searches `D:\REALPROJECTS\tflex_api\llm`.
- `get_tflex_environment` / `python -m tflex_harness.cli env` — checks docs, DLLs, compilers, runner skeleton build/env probe, and process state.
- `run_csharp_tflex` / `python -m tflex_harness.cli run-csharp` — compiles and runs visible C# snippets via `csc.exe`, with successful builds cached by content hash.
- `list_tflex_recipes` / `python -m tflex_harness.cli recipes` — lists verified recipes.
- `run_tflex_recipe` / `python -m tflex_harness.cli run-recipe` — runs verified recipes.
- `capture_tflex_state` / `python -m tflex_harness.cli state` — captures read-only live session/document state, document list, aggregate 2D/3D/variable counts, observed 2D/3D type counts, 3D operation bounding boxes when documents are open, empty selection, and run artifacts.
- `save_tflex_snippet_candidate` / `python -m tflex_harness.cli save-snippet` — saves a visible C# candidate under `agent_workspace/snippets` for later docs review, compile/run evidence, and promotion to a verified recipe.
- `python -m tflex_harness.cli reverse-evidence` — turns GRB contour evidence JSON into a semantic model and readable parametric C# where shapes are recognized.
- `python -m tflex_harness.cli prototypes-scan` — scans the installed T-FLEX prototype corpus, preserves Cyrillic relative paths, computes SHA256 hashes, and writes `catalog.json`.
- `python -m tflex_harness.cli prototypes-list` — lists prototypes by category and extension.
- `python -m tflex_harness.cli prototypes-info` — resolves one prototype by id, name, relative path, or absolute path.
- `python -m tflex_harness.cli prototypes-open-save-batch` — batch validates safe copy/open/save for `.grb` prototypes and writes JSON/CSV validation matrices.
- `python -m tflex_harness.cli prototypes-title-batch` — batch copies `.grb` prototypes, sets `Document.Properties.Title`, saves, reopens, verifies persistence, and writes JSON/CSV mutation matrices.
- `python -m tflex_harness.cli prototypes-table-cell-batch` — batch mutates one `RichText` table cell on copied `.grb` prototypes and writes JSON/CSV matrices.
- `python -m tflex_harness.cli prototypes-specification-bom-field-batch` — batch mutates one `BOMObject` standard field on copied specification `.grb` prototypes and writes support buckets.
- `python -m tflex_harness.cli prototypes-first-visible-text-batch` — batch replaces first API-visible non-table text on copied `.grb` prototypes and writes JSON/CSV matrices.
- `python -m tflex_harness.cli prototypes-metadata` — opens copied `.grb` prototypes and extracts document/page/2D/3D/variable/fragment metadata into JSON/CSV indexes.
- `create_tflex_document` / `python -m tflex_harness.cli create-document --payload input.json` — dispatches a document factory JSON payload to one verified prototype recipe, writes `input_payload.json` and `factory_plan.json`, and can run live or `--dry-run`.
- `python -m tflex_harness.cli document-factory-samples` — runs the standard 3D/drawing/specification/table factory sample payloads and writes a JSON/CSV matrix.
- `run_tflex_document_factory_batch` / `python -m tflex_harness.cli document-factory-batch --payload-dir payloads` — runs every payload JSON in a folder, classifies failures, supports rerun-failed/open-only audit, and writes JSON/CSV/report artifacts.

The MCP server entrypoint is `tflex-harness-mcp` and maps to `tflex_harness.mcp_server:main`.

Recipe `output_file` arguments are intentionally constrained to `artifacts/tflex_docs/...`; the harness rejects paths outside that tree so live runs do not write random files into the repository or user folders.

Snippet runs receive:

- `TFLEX_HARNESS_RUN_DIR` — per-run artifact root.
- `TFLEX_HARNESS_ARTIFACTS_DIR` — writable folder for snippet-generated files.

`result.json` includes `build_log`, `stdout_path`, `stderr_path`, `run_log`, `artifacts_dir`, and discovered files under `artifacts/`.
Timeouts are structured as `stage: "timeout"` with `phase: "compile"` or `phase: "run"`.
Each `run-csharp` / `run_csharp_tflex` call also appends a compact event to `logs/events.jsonl` with stage, phase, run directory, cache info, diagnostic count, and artifact count.

## C# snippet helpers

Reusable helper source files live under `src/tflex_harness/csharp_helpers`.
They are compiled as C# source together with the visible snippet, not hidden behind a precompiled CAD wrapper.

Use helper sets with CLI:

```powershell
python -m tflex_harness.cli run-csharp --mode compile_only --helper easy_core --code "using TFlexEasy; public class Program { public static int Main(){ System.Console.WriteLine(EasyUnits.F(1)); return 0; } }"
```

Initial helper sets:

- `easy_core` — `TFlexEasyUnits.cs`, `TFlexEasyDiagnostics.cs`
- `easy_session` — core helpers plus `TFlexEasySession.cs`
- `easy_3d` — session/profile/gear/solid/placement helpers
- `easy_gears` — direct-XY trapezoid gear helpers, tooth phase helpers, and gear clearance diagnostics
- `easy_export` — session/export helpers
- `easy_prototype` — safe copy/open/save helpers for installed `.grb` prototypes
- `easy_variables` — prototype/session helpers plus text/real variable mutation helpers
- `easy_text` — prototype/session helpers plus `RichText` table cell and visible 2D text replacement helpers
- `easy_document_properties` — prototype/session helpers plus writable `Document.Properties` string mutation helpers
- `all` — all helper source files

Every helper run copies helper `.cs` files into the run directory under `helpers/`, includes helper source content in the compile cache key, and records helper paths plus SHA256 hashes in `result.json`.

For gear assemblies, prefer `TFlexEasyGears.cs` direct-XY profile helpers over creating centered profiles and moving the resulting gear bodies. Direct-XY gear profiles make saved `.grb`/STEP artifacts easier to inspect and avoid ambiguous visual placement from body transformations. Use explicit tooth phases such as `EasyGears.PhaseForGapAtAxisDeg(...)` and `EasyGears.PlanetToothFacingSunPhaseDeg(...)` instead of hand-guessing rotations.

## GRB reverse prototypes

`src/tflex_harness/grb_reverse.py` recognizes contour evidence extracted from legacy `.grb` files and emits:

- `semantic_model.json`
- readable `parametric_candidate.cs`

Example:

```powershell
python -m tflex_harness.cli reverse-evidence agent_workspace/snippets/grb_reverse_planetary/model_evidence_with_contours.json --output-dir agent_workspace/snippets/grb_reverse_planetary/semantic_parametric
```

This is not full design-intent decompilation. Recognized shapes become helper calls; unknown geometry should fall back to raw contour reconstruction.

## T-FLEX prototype corpus

Installed T-FLEX document prototypes are treated as a reference corpus:

```text
C:\Program Files\T-FLEX CAD 17\Program\Прототипы
```

Scan them with:

```powershell
python -m tflex_harness.cli prototypes-scan
python -m tflex_harness.cli prototypes-list --category Чертежи
python -m tflex_harness.cli prototypes-info "Чертежи/Чертёж детали с форматкой"
python -m tflex_harness.cli prototypes-open-save-batch --dry-run
python -m tflex_harness.cli prototypes-title-batch --dry-run
python -m tflex_harness.cli prototypes-metadata --limit 1
```

Verified local scan on 2026-05-25:

- `file_count=57`
- `.grb=50`
- `.ico=5`
- `.txt=1`
- `.xml=1`
- output: `artifacts/prototype_catalog/current_probe/catalog.json`

Verified live open/copy/save batch on 2026-05-25:

- command: `python -m tflex_harness.cli prototypes-open-save-batch --timeout-sec 120 --output-dir artifacts/prototype_validation/live_all_20260525`
- selected `.grb`: `50`
- attempted: `50`
- passed: `50`
- failed: `0`
- matrix: `artifacts/prototype_validation/live_all_20260525/prototype_open_save_matrix.json`
- csv: `artifacts/prototype_validation/live_all_20260525/prototype_open_save_matrix.csv`

Verified live title-mutation batch on 2026-05-25:

- command: `python -m tflex_harness.cli prototypes-title-batch --timeout-sec 120 --fail-fast`
- selected `.grb`: `50`
- attempted: `50`
- passed: `50`
- failed: `0`
- persisted: `50`
- property: `Title`
- matrix: `artifacts/prototype_validation/20260525_215002_183343/prototype_title_mutation_matrix.json`
- csv: `artifacts/prototype_validation/20260525_215002_183343/prototype_title_mutation_matrix.csv`
- follow-up artifact-column live check: `python -m tflex_harness.cli prototypes-title-batch --limit 1 --timeout-sec 120`, matrix `artifacts/prototype_validation/20260525_215156_953215/prototype_title_mutation_matrix.json`

Verified live table-cell batches on 2026-05-25:

- command: `python -m tflex_harness.cli prototypes-table-cell-batch --category Таблицы --timeout-sec 120 --fail-fast`
- table result: selected `7`, attempted `7`, passed `7`, failed `0`, persisted `7`
- table matrix: `artifacts/prototype_validation/20260525_220550_733488/prototype_table_cell_matrix.json`
- command: `python -m tflex_harness.cli prototypes-table-cell-batch --category Спецификации --timeout-sec 120`
- specification result: selected `20`, attempted `20`, passed `1`, failed `19`, persisted `1`
- specification matrix: `artifacts/prototype_validation/20260525_220918_092578/prototype_table_cell_matrix.json`

Verified live specification BOM-field path on 2026-05-26:

- probe command: `python -m tflex_harness.cli run-recipe prototype_probe_specification_objects --arg 'prototype_id=Спецификации/Спецификация форма 1 ГОСТ 2.106-2019' --timeout-sec 120`
- probe run: `artifacts/runs/20260526_210936_525247_recipe_prototype_probe_specification_objects`
- probe evidence: `object.6.type=TFlex.Model.Model2D.BOMObject`; raw `RichText.GetTableByIndex(0)` failed with `InvalidOperationException: Can not find object / Bad position`
- mutation command: `python -m tflex_harness.cli run-recipe prototype_set_specification_bom_field --arg 'prototype_id=Спецификации/Спецификация форма 1 ГОСТ 2.106-2019' --arg 'standard_field=Desc' --arg 'text_value=Harness Spec BOM Desc' --arg 'add_record=true' --timeout-sec 120`
- mutation run: `artifacts/runs/20260526_211159_374848_recipe_prototype_set_specification_bom_field`
- mutation evidence: `spec.record.added=True`, `spec.field.after=Harness Spec BOM Desc`, `spec.field.reopened=Harness Spec BOM Desc`, `spec.field.persisted=True`
- batch command: `python -m tflex_harness.cli prototypes-specification-bom-field-batch --category Спецификации --timeout-sec 120`
- first batch result: selected `20`, attempted `20`, passed `17`, failed `3`, persisted `17`
- first buckets: `bom_standard_field_supported=17`, `bom_no_persist=3`
- first matrix: `artifacts/prototype_validation/20260526_211323_125648/prototype_specification_bom_field_matrix.json`
- scan-based command: `python -m tflex_harness.cli prototypes-specification-bom-field-batch --category Спецификации --timeout-sec 120`
- scan-based result: selected `20`, attempted `20`, passed `20`, failed `0`, persisted `20`
- scan-based buckets: `bom_standard_field_supported=20`
- scan-based matrix: `artifacts/prototype_validation/20260526_212016_705556/prototype_specification_bom_field_matrix.json`

Verified live electrical visible-text batch on 2026-05-25:

- command: `python -m tflex_harness.cli prototypes-first-visible-text-batch --category Электротехника --timeout-sec 120`
- result: selected `8`, attempted `8`, passed `4`, failed `4`, persisted `4`
- matrix: `artifacts/prototype_validation/20260525_220808_834096/prototype_first_visible_text_matrix.json`
- direct recipe proof: `artifacts/runs/20260525_220841_828547_recipe_prototype_replace_first_visible_text`, `firstVisibleText.persisted=True`
- electrical object probe: `artifacts/runs/20260526_212519_855910_recipe_prototype_probe_electrical_objects`, classified `Электротехника/Аппарат` as variable-backed (`$Наименование`, `$Обозначение`, `$Tip_Doc`, `$Vid`)
- variable-backed mutation proof: `artifacts/runs/20260526_212542_998623_recipe_prototype_set_text_variable`, `variable.reopened=Harness Electrical Name`, `variable.persisted=True`
- electrical fallback batch command: `python -m tflex_harness.cli prototypes-electrical-labels-batch --category Электротехника --timeout-sec 120`
- electrical fallback batch result: selected `8`, attempted `8`, passed `8`, failed `0`, persisted `8`; buckets `visible_text_supported=4`, `variable_backed_supported=4`
- electrical fallback matrix: `artifacts/prototype_validation/20260526_213248_774110/prototype_electrical_labels_matrix.json`

Verified live fragment assembly semantic insertion on 2026-05-25:

- command: `python -m tflex_harness.cli run-recipe helper_fragment_lcs_assembly --timeout-sec 120`
- run: `artifacts/runs/20260525_220748_356485_recipe_helper_fragment_lcs_assembly`
- evidence: `fragment.sourceLcs=FRAG_LCS`, `fragment.targetLcsNull=False`, `assembly.operationsAfter=1`, `assembly.saved=True`, `fragmentAssembly.persisted=True`

Verified live fragment LCS factory payload on 2026-05-26:

- payload: `agent_workspace/payloads/fragment_lcs_assembly.json`
- direct command: `python -m tflex_harness.cli create-document --payload agent_workspace/payloads/fragment_lcs_assembly.json --timeout-sec 120`
- direct factory run: `artifacts/runs/20260526_213859_133554_document_factory`
- generated snippet run: `artifacts/runs/20260526_213859_145299_factory_fragment_lcs_assembly`
- evidence: `factory.fragment.sourceLcsAfterFix=FRAG_LCS`, `factory.fragment.targetLcsNullAfterFix=False`, `factory.fragment.reopened=True`, `factory.fragment.reopenedOperations=1`, `factory.fragment.persisted=True`
- outputs: `factory_fragment_lcs_assembly.grb`, `factory_fragment_lcs_assembly.step`
- batch command: `python -m tflex_harness.cli document-factory-batch --payload-dir agent_workspace/payloads --timeout-sec 120`
- batch matrix: `artifacts/document_factory_batches/20260526_213924_474008/document_factory_batch_matrix.json`
- batch result: selected `1`, attempted `1`, passed `1`, failed `0`; output formats `grb`, `step`


Verified live assembly validation MVP on 2026-05-26:

- command: `python -m tflex_harness.cli run-recipe helper_assembly_validation --timeout-sec 120`
- run: `artifacts/runs/20260526_231540_012426_recipe_helper_assembly_validation`
- helper set: `easy_assembly_validation`
- helper source: `src/tflex_harness/csharp_helpers/TFlexEasyAssemblyValidation.cs`
- bad assembly evidence: `bad.pair.0_1.solid.0_0.clash.0.type=Interfere`, `bad.summary.clashPairCount=1`, `bad.summary.collisionCount=1`, `bad.summary.floatingFragmentCount=1`, `bad.expectedDetected=True`
- bad floating reason: `bad.fragment.1.connectedByMate=False`, `bad.fragment.1.reason=no_lcs_fixing_or_mate`
- good assembly evidence: `good.summary.bboxOverlapCount=0`, `good.summary.collisionCount=0`, `good.summary.floatingFragmentCount=0`, `good.expectedClean=True`
- mate inspector evidence: `bad.summary.mateCount=0`, `good.summary.mateCount=0`, `good.summary.mateLinkedFragmentCount=0`
- final evidence: `assemblyValidation.live=True`
- collision path: AABB broad phase plus exact `BaseBody.Clash(...)`; mate graph hook uses `Document3D.GetMates(doc)`, but positive native mate-edge case is not live-proven yet.

Verified live metadata batch on 2026-05-25:

- command: `python -m tflex_harness.cli prototypes-metadata --timeout-sec 120 --output-dir artifacts/prototype_metadata/live_all_20260525`
- selected `.grb`: `50`
- attempted: `50`
- passed: `50`
- failed: `0`
- index: `artifacts/prototype_metadata/live_all_20260525/prototype_metadata_index.json`
- csv: `artifacts/prototype_metadata/live_all_20260525/prototype_metadata_index.csv`
- per-prototype JSON dir: `artifacts/prototype_metadata/live_all_20260525/metadata`

The source `Program Files` tree is read-only input. Future prototype automation must copy selected `.grb` files into a run artifact directory before opening or saving.

## Verified recipes

- `environment_probe` — initializes and exits a minimal read-only API session.
- `create_empty_document` — creates an invisible empty 2D document, saves it as `.grb`, closes it, and exits the session.
- `save_document_as_temp` — creates a hidden temporary 2D document, verifies `SaveAs` to a `.grb` artifact path, writes a snippet artifact marker, closes the document, and exits the session.
- `create_simple_2d_line` — creates two free 2D nodes, a construction line through them, verifies `Get2DObjects()` count/types, saves `.grb`, closes the document, and exits the session.
- `create_simple_3d_extrusion` — creates a hidden 3D document, builds a circular area profile on a standard workplane, verifies one `ThickenExtrusion` operation with non-null body/geometry and positive bounding box, saves `.grb`, closes the document, and exits the session.
- `prototype_open_copy_save` — copies an installed `.grb` prototype to the run artifact directory, opens the copy, saves a new `.grb`, closes it, and prints source/copy/output SHA evidence. Use `--arg source_path=...` or `--arg prototype_id=...`.
- `prototype_set_text_variable` — copies an installed `.grb` prototype, opens the copy, sets one existing text variable, saves a new `.grb`, reopens it, and verifies persisted `TextValue`. Use single quotes around PowerShell args containing `$`, for example `--arg 'variable_name=$Наименование'`.
- `prototype_set_real_variable` — copies an installed `.grb` prototype, opens the copy, sets one existing real-number variable, saves a new `.grb`, reopens it, and verifies persisted `RealValue`.
- `prototype_set_table_cell` — copies an installed table prototype, opens the copy, edits one cell in the first `RichText` table, saves a new `.grb`, reopens it, and verifies persisted cell text.
- `prototype_set_document_property` — copies an installed `.grb` prototype, opens the copy, sets one writable string property on `Document.Properties`, saves a new `.grb`, reopens it, and verifies persisted property text.
- `prototype_replace_visible_text` — copies an installed `.grb` prototype, opens the copy, replaces visible `LineText`/non-table `RichText`, saves a new `.grb`, reopens it, and verifies persisted replacement.
- `create_detail_drawing_from_prototype` — category recipe for drawings; defaults to `Чертежи/Чертёж детали с форматкой`, sets `Document.Properties.Title`, saves, reopens, and verifies.
- `create_specification_from_prototype` — category recipe for specifications; defaults to `Спецификации/Спецификация форма 1 ГОСТ 2.106-2019`, sets `Document.Properties.Title`, saves, reopens, and verifies.
- `create_3d_part_from_prototype` — category recipe for 3D parts; defaults to `3D Деталь`, sets `Document.Properties.Title`, saves, reopens, and verifies.
- `create_table_document_from_prototype` — category recipe for table documents; defaults to `Таблицы/Таблица параметров зубчатого колеса.grb`, edits one `RichText` table cell, saves, reopens, and verifies.
- `create_electrical_doc_from_prototype` — category recipe for electrical docs; defaults to `Электротехника/Клеммник.grb`, replaces visible text, saves, reopens, and verifies.
- `create_3d_assembly_from_prototype` — category recipe for 3D assemblies; defaults to `3D Сборка`, sets `Document.Properties.Title`, saves, reopens, and verifies.
- `create_2d_assembly_from_prototype` — category recipe for 2D assemblies; defaults to `2D Сборка`, sets `Document.Properties.Title`, saves, reopens, and verifies.
- `create_fragment_3d_part_from_prototype` — category recipe for 3D part fragments; defaults to `Фрагменты/3D Деталь.grb`, sets `Document.Properties.Title`, saves, reopens, and verifies.
- `create_fragment_3d_assembly_from_prototype` — category recipe for 3D assembly fragments; defaults to `Фрагменты/3D Сборка.grb`, sets `Document.Properties.Title`, saves, reopens, and verifies.
- `create_fragment_sheet_metal_part_from_prototype` — category recipe for sheet-metal fragments; defaults to `Фрагменты/Листовая Деталь.grb`, sets `Document.Properties.Title`, saves, reopens, and verifies.
- `create_assembly_drawing_from_prototype` — category recipe for assembly drawings; defaults to `Чертежи/Сборочный чертёж с форматкой.grb`, sets `Document.Properties.Title`, saves, reopens, and verifies.
- `create_2d_detail_from_prototype` — category recipe for 2D details; defaults to `2D Деталь`, sets `Document.Properties.Title`, saves, reopens, and verifies.
- `create_sheet_metal_part_from_prototype` — category recipe for sheet-metal parts; defaults to `Листовая Деталь`, sets `Document.Properties.Title`, saves, reopens, and verifies.
- `create_assembly_drawing_with_spec_from_prototype` — category recipe for assembly drawings with specification; defaults to `Чертежи/Сборочный чертёж со спецификацией.grb`, sets `Document.Properties.Title`, saves, reopens, and verifies.
- `create_text_document_from_prototype` — category recipe for text documents; defaults to `Чертежи/Текстовый документ с форматкой.grb`, sets `Document.Properties.Title`, saves, reopens, and verifies.
- `create_tech_sketch_card_from_prototype` — category recipe for tech sketch cards; defaults to `Техкарты/Карта эскизов ГОСТ 3.1105-2011 Ф7-7а.grb`, sets `Document.Properties.Title`, saves, reopens, and verifies.

Verified live text-variable mutation on 2026-05-25:

- command: `python -m tflex_harness.cli run-recipe prototype_set_text_variable --arg 'prototype_id=2D Деталь' --arg 'variable_name=$Наименование' --arg 'text_value=Harness Recipe Test' --timeout-sec 120`
- live run directory: `artifacts/runs/20260525_175508_317973_recipe_prototype_set_text_variable`
- source prototype: `C:\Program Files\T-FLEX CAD 17\Program\Прототипы\2D Деталь.grb`
- verified stdout: `variable.exists=True`, `variable.set=True`, `document.saved=True`, `variable.reopened=Harness Recipe Test`, `variable.persisted=True`

Verified live real-variable mutation on 2026-05-25:

- command: `python -m tflex_harness.cli run-recipe prototype_set_real_variable --arg 'prototype_id=2D Деталь' --arg 'variable_name=Nomer_Shem' --arg 'real_value=42' --timeout-sec 120`
- live run directory: `artifacts/runs/20260525_180343_657081_recipe_prototype_set_real_variable`
- source prototype: `C:\Program Files\T-FLEX CAD 17\Program\Прототипы\2D Деталь.grb`
- verified stdout: `variable.exists=True`, `variable.expression.Nomer_Shem=42`, `variable.set=True`, `document.saved=True`, `variable.reopened=42`, `variable.persisted=True`

Verified live table-cell mutation on 2026-05-25:

- command: `python -m tflex_harness.cli run-recipe prototype_set_table_cell --arg 'prototype_id=Таблицы/Таблица параметров зубчатого колеса.grb' --arg 'cell_index=2' --arg 'text_value=Harness Table Test' --timeout-sec 120`
- live run directory: `artifacts/runs/20260525_181242_346840_recipe_prototype_set_table_cell`
- source prototype: `C:\Program Files\T-FLEX CAD 17\Program\Прототипы\Таблицы\Таблица параметров зубчатого колеса.grb`
- verified stdout: `richText.count=1`, `table.cell.after=Harness Table Test`, `table.cell.set=True`, `document.saved=True`, `table.cell.reopened=Harness Table Test`, `table.cell.persisted=True`

Verified live document-property mutation on 2026-05-25:

- command: `python -m tflex_harness.cli run-recipe prototype_set_document_property --arg 'prototype_id=2D Деталь' --arg 'property_name=Title' --arg 'text_value=Harness Document Property Test' --timeout-sec 120`
- live run directory: `artifacts/runs/20260525_181851_320860_recipe_prototype_set_document_property`
- source prototype: `C:\Program Files\T-FLEX CAD 17\Program\Прототипы\2D Деталь.grb`
- verified stdout: `documentProperty.exists=True`, `documentProperty.after.Title=Harness Document Property Test`, `documentProperty.set=True`, `document.saved=True`, `documentProperty.reopened=Harness Document Property Test`, `documentProperty.persisted=True`

Verified live visible 2D text replacement on 2026-05-25:

- command: `python -m tflex_harness.cli run-recipe prototype_replace_visible_text --arg 'prototype_id=Электротехника/Клеммник.grb' --arg 'search_text=Цепь' --arg 'replacement_text=Harness Circuit' --timeout-sec 120`
- live run directory: `artifacts/runs/20260525_182531_611149_recipe_prototype_replace_visible_text`
- source prototype: `C:\Program Files\T-FLEX CAD 17\Program\Прототипы\Электротехника\Клеммник.grb`
- verified stdout: `visibleText.beforeCount=1`, `visibleText.line.after=Harness Circuit`, `visibleText.replaceCount=1`, `document.saved=True`, `visibleText.oldAfter=0`, `visibleText.newAfter=1`, `visibleText.persisted=True`

Verified live category recipes on 2026-05-25:

- command: `python -m tflex_harness.cli run-recipe create_detail_drawing_from_prototype --timeout-sec 120`
- live run directory: `artifacts/runs/20260525_212201_368610_recipe_create_detail_drawing_from_prototype`
- source prototype: `C:\Program Files\T-FLEX CAD 17\Program\Прототипы\Чертежи\Чертёж детали с форматкой.grb`
- verified stdout: `documentProperty.after.Title=Harness Detail Drawing`, `document.saved=True`, `document.outputSize=25462`, `documentProperty.persisted=True`
- command: `python -m tflex_harness.cli run-recipe create_specification_from_prototype --timeout-sec 120`
- live run directory: `artifacts/runs/20260525_212204_093117_recipe_create_specification_from_prototype`
- source prototype: `C:\Program Files\T-FLEX CAD 17\Program\Прототипы\Спецификации\Спецификация форма 1 ГОСТ 2.106-2019.grb`
- verified stdout: `documentProperty.after.Title=Harness Specification`, `document.saved=True`, `document.outputSize=29138`, `documentProperty.persisted=True`
- command: `python -m tflex_harness.cli run-recipe create_3d_part_from_prototype --timeout-sec 120`
- live run directory: `artifacts/runs/20260525_213236_790332_recipe_create_3d_part_from_prototype`
- source prototype: `C:\Program Files\T-FLEX CAD 17\Program\Прототипы\3D Деталь.grb`
- verified stdout: `documentProperty.after.Title=Harness 3D Part`, `document.saved=True`, `document.outputSize=28573`, `documentProperty.persisted=True`
- command: `python -m tflex_harness.cli run-recipe create_table_document_from_prototype --timeout-sec 120`
- live run directory: `artifacts/runs/20260525_213238_919912_recipe_create_table_document_from_prototype`
- source prototype: `C:\Program Files\T-FLEX CAD 17\Program\Прототипы\Таблицы\Таблица параметров зубчатого колеса.grb`
- verified stdout: `richText.count=1`, `table.cell.after=Harness Table Document`, `document.saved=True`, `document.outputSize=63263`, `table.cell.persisted=True`
- command: `python -m tflex_harness.cli run-recipe create_electrical_doc_from_prototype --timeout-sec 120`
- live run directory: `artifacts/runs/20260525_213241_046854_recipe_create_electrical_doc_from_prototype`
- source prototype: `C:\Program Files\T-FLEX CAD 17\Program\Прототипы\Электротехника\Клеммник.grb`
- verified stdout: `visibleText.replaceCount=1`, `document.saved=True`, `document.outputSize=58724`, `visibleText.newAfter=1`, `visibleText.persisted=True`
- command: `python -m tflex_harness.cli run-recipe create_3d_assembly_from_prototype --timeout-sec 120`
- live run directory: `artifacts/runs/20260525_214100_314774_recipe_create_3d_assembly_from_prototype`
- source prototype: `C:\Program Files\T-FLEX CAD 17\Program\Прототипы\3D Сборка.grb`
- verified stdout: `documentProperty.after.Title=Harness 3D Assembly`, `document.saved=True`, `document.outputSize=28657`, `documentProperty.persisted=True`
- command: `python -m tflex_harness.cli run-recipe create_2d_assembly_from_prototype --timeout-sec 120`
- live run directory: `artifacts/runs/20260525_214103_281473_recipe_create_2d_assembly_from_prototype`
- source prototype: `C:\Program Files\T-FLEX CAD 17\Program\Прототипы\2D Сборка.grb`
- verified stdout: `documentProperty.after.Title=Harness 2D Assembly`, `document.saved=True`, `document.outputSize=22489`, `documentProperty.persisted=True`
- command: `python -m tflex_harness.cli run-recipe create_fragment_3d_part_from_prototype --timeout-sec 120`
- live run directory: `artifacts/runs/20260525_214105_435010_recipe_create_fragment_3d_part_from_prototype`
- source prototype: `C:\Program Files\T-FLEX CAD 17\Program\Прототипы\Фрагменты\3D Деталь.grb`
- verified stdout: `documentProperty.after.Title=Harness Fragment 3D Part`, `document.saved=True`, `document.outputSize=27850`, `documentProperty.persisted=True`
- command: `python -m tflex_harness.cli run-recipe create_fragment_3d_assembly_from_prototype --timeout-sec 120`
- live run directory: `artifacts/runs/20260525_214107_547016_recipe_create_fragment_3d_assembly_from_prototype`
- source prototype: `C:\Program Files\T-FLEX CAD 17\Program\Прототипы\Фрагменты\3D Сборка.grb`
- verified stdout: `documentProperty.after.Title=Harness Fragment 3D Assembly`, `document.saved=True`, `document.outputSize=23888`, `documentProperty.persisted=True`
- command: `python -m tflex_harness.cli run-recipe create_fragment_sheet_metal_part_from_prototype --timeout-sec 120`
- live run directory: `artifacts/runs/20260525_214109_723882_recipe_create_fragment_sheet_metal_part_from_prototype`
- source prototype: `C:\Program Files\T-FLEX CAD 17\Program\Прототипы\Фрагменты\Листовая Деталь.grb`
- verified stdout: `documentProperty.after.Title=Harness Fragment Sheet Metal Part`, `document.saved=True`, `document.outputSize=27593`, `documentProperty.persisted=True`
- command: `python -m tflex_harness.cli run-recipe create_assembly_drawing_from_prototype --timeout-sec 120`
- live run directory: `artifacts/runs/20260525_214112_134234_recipe_create_assembly_drawing_from_prototype`
- source prototype: `C:\Program Files\T-FLEX CAD 17\Program\Прототипы\Чертежи\Сборочный чертёж с форматкой.grb`
- verified stdout: `documentProperty.after.Title=Harness Assembly Drawing`, `document.saved=True`, `document.outputSize=25809`, `documentProperty.persisted=True`
- command: `python -m tflex_harness.cli run-recipe create_2d_detail_from_prototype --timeout-sec 120`
- live run directory: `artifacts/runs/20260525_214436_007919_recipe_create_2d_detail_from_prototype`
- source prototype: `C:\Program Files\T-FLEX CAD 17\Program\Прототипы\2D Деталь.grb`
- verified stdout: `documentProperty.after.Title=Harness 2D Detail`, `document.saved=True`, `document.outputSize=23230`, `documentProperty.persisted=True`
- command: `python -m tflex_harness.cli run-recipe create_sheet_metal_part_from_prototype --timeout-sec 120`
- live run directory: `artifacts/runs/20260525_214438_176369_recipe_create_sheet_metal_part_from_prototype`
- source prototype: `C:\Program Files\T-FLEX CAD 17\Program\Прототипы\Листовая Деталь.grb`
- verified stdout: `documentProperty.after.Title=Harness Sheet Metal Part`, `document.saved=True`, `document.outputSize=28418`, `documentProperty.persisted=True`
- command: `python -m tflex_harness.cli run-recipe create_assembly_drawing_with_spec_from_prototype --timeout-sec 120`
- live run directory: `artifacts/runs/20260525_214440_312277_recipe_create_assembly_drawing_with_spec_from_prototype`
- source prototype: `C:\Program Files\T-FLEX CAD 17\Program\Прототипы\Чертежи\Сборочный чертёж со спецификацией.grb`
- verified stdout: `documentProperty.after.Title=Harness Assembly Drawing With Spec`, `document.saved=True`, `document.outputSize=47462`, `documentProperty.persisted=True`
- command: `python -m tflex_harness.cli run-recipe create_text_document_from_prototype --timeout-sec 120`
- live run directory: `artifacts/runs/20260525_214442_368731_recipe_create_text_document_from_prototype`
- source prototype: `C:\Program Files\T-FLEX CAD 17\Program\Прототипы\Чертежи\Текстовый документ с форматкой.grb`
- verified stdout: `documentProperty.after.Title=Harness Text Document`, `document.saved=True`, `document.outputSize=20120`, `documentProperty.persisted=True`
- command: `python -m tflex_harness.cli run-recipe create_tech_sketch_card_from_prototype --timeout-sec 120`
- live run directory: `artifacts/runs/20260525_214444_473242_recipe_create_tech_sketch_card_from_prototype`
- source prototype: `C:\Program Files\T-FLEX CAD 17\Program\Прототипы\Техкарты\Карта эскизов ГОСТ 3.1105-2011 Ф7-7а.grb`
- verified stdout: `documentProperty.after.Title=Harness Tech Sketch Card`, `document.saved=True`, `document.outputSize=42281`, `documentProperty.persisted=True`

## Document factory payloads

Initial Phase 6 factory command:

```powershell
python -m tflex_harness.cli create-document --payload input.json --dry-run
python -m tflex_harness.cli create-document --payload input.json --timeout-sec 120
python -m tflex_harness.cli document-factory-batch --payload-dir payloads --dry-run
python -m tflex_harness.cli document-factory-batch --payload-dir payloads --timeout-sec 120 --fail-fast
python -m tflex_harness.cli document-factory-batch --failed-matrix artifacts/my_batch/document_factory_batch_matrix.json --timeout-sec 120
python -m tflex_harness.cli document-factory-batch --payload-dir payloads --audit-open-only --timeout-sec 120
```

Current dispatcher executes one generated multi-step C# snippet when a payload contains multiple supported mutation operations. Single-operation payloads dispatch to one verified recipe. Single-operation priority is:

1. explicit `recipe`;
2. `document.properties`;
3. `document.variables`;
4. `document.text_replacements`;
5. `document.tables`;
6. fallback `prototype_open_copy_save`.

Multi-step runs apply all supported operations to one copied `.grb`, save once, reopen, and validate all mutations.

Payload `output` currently supports named GRB, STEP, PDF, DXF, and DWG materialization:

```json
{
  "output": {
    "name": "customer_document.grb",
    "exports": ["grb", "step", "pdf", "dxf", "dwg"]
  }
}
```

The factory copies the recipe/snippet saved `.grb` into the factory run as
`artifacts/outputs/<sanitized-name>.grb` and records it in the top-level
`outputs` array. For `step`, `pdf`, `dxf`, and `dwg`, it opens the saved `.grb`
in a separate visible C# export run via `TFlexEasyExport.cs`, then records
`artifacts/outputs/<sanitized-name>.<format>`. `step` uses
`Document.ExportToSTEP.Export(...)`. `dxf` and `dwg` use
`Document.ExportToDXF.Export(...)` and `Document.ExportToDWG.Export(...)`.
For `pdf`, it uses `new ExportToPDF(document).Export(...)`; the helper copies
`PDFExport.dll` from the T-FLEX program directory to the snippet run directory
first because live evidence showed the PDF module loader requires a local
module copy. Unsupported export formats are rejected at plan time.

Batch factory runs use the same payload contract for every `.json` in a folder:

```powershell
python -m tflex_harness.cli document-factory-batch --payload-dir payloads --glob *.json --recursive --timeout-sec 120 --output-dir artifacts/my_batch
```

The batch command writes `document_factory_batch_matrix.json` and
`document_factory_batch_matrix.csv` with per-payload status, recipe selection,
output paths/sizes, export errors, failure kind, and factory run directory. It
also writes `document_factory_failure_report.json`, a smaller machine-readable
failure report with failed payload paths grouped by `failure_kind` and a rerun
hint. The summary includes buckets for `passed`, `input_failed`,
`timeout_failed`, `export_failed`, `recipe_failed`, `run_failed`, and
`unknown_failed`. Use `--dry-run` for planning only, `--fail-fast` to stop after
the first failed payload, and `--failed-matrix <previous-matrix.json>` to rerun
only rows where `ok=false`. Use `--audit-open-only` to resolve each payload
prototype and run the metadata open probe only; this mode does not apply
mutations, save GRB, or export files, and records metadata counts such as 2D
object, 3D operation, variable, and page totals.

Verified live factory dispatch on 2026-05-25:

- command: `python -m tflex_harness.cli create-document --payload artifacts/factory_payloads/phase6_property_payload.json --timeout-sec 120`
- factory run directory: `artifacts/runs/20260525_183154_667605_document_factory`
- recipe run directory: `artifacts/runs/20260525_183154_769543_recipe_prototype_set_document_property`
- selected recipe: `prototype_set_document_property`
- verified stdout: `documentProperty.after.Title=Harness Factory Live Test`, `document.saved=True`, `documentProperty.reopened=Harness Factory Live Test`, `documentProperty.persisted=True`

Verified live named GRB output on 2026-05-25:

- command: `python -m tflex_harness.cli create-document --payload artifacts/factory_payloads/phase6_named_grb_payload.json --timeout-sec 120`
- factory run directory: `artifacts/runs/20260525_184829_962489_document_factory`
- recipe run directory: `artifacts/runs/20260525_184830_053534_recipe_prototype_set_document_property`
- materialized output: `artifacts/runs/20260525_184829_962489_document_factory/artifacts/outputs/phase6_named_output.grb`
- verified output evidence: `outputs[0].format=grb`, `outputs[0].relative_path=artifacts/outputs/phase6_named_output.grb`, `outputs[0].size=23240`, `output_errors=[]`

Verified live STEP output on 2026-05-25:

- prototype-copy command: `python -m tflex_harness.cli create-document --payload artifacts/factory_payloads/phase6_3d_step_payload.json --timeout-sec 120`
- prototype-copy factory run: `artifacts/runs/20260525_190649_137237_document_factory`
- prototype-copy STEP output: `artifacts/outputs/phase6_3d_step_export.step`, size `322`
- solid explicit-recipe command: `python -m tflex_harness.cli create-document --payload artifacts/factory_payloads/phase6_solid_step_payload.json --timeout-sec 120`
- solid explicit-recipe factory run: `artifacts/runs/20260525_190913_994364_document_factory`
- solid STEP export run: `artifacts/runs/20260525_190915_851463_factory_step_export`
- solid STEP output: `artifacts/outputs/phase6_solid_step_export.step`, size `6919`
- solid STEP content evidence: contains `MANIFOLD_SOLID_BREP`, `CLOSED_SHELL`, and `ADVANCED_FACE`
- note: T-FLEX `ExportToSTEP.Export(...)` returned `False` while still writing valid non-empty STEP, so success is based on file existence and size, matching existing helper evidence.

Verified live PDF output on 2026-05-25:

- command: `python -m tflex_harness.cli create-document --payload artifacts/factory_payloads/phase6_drawing_pdf_payload.json --timeout-sec 120`
- factory run: `artifacts/runs/20260525_192244_448383_document_factory`
- recipe run: `artifacts/runs/20260525_192244_524243_recipe_prototype_set_document_property`
- PDF export run: `artifacts/runs/20260525_192245_937700_factory_pdf_export`
- PDF output: `artifacts/outputs/phase6_drawing_pdf_export.pdf`, size `11109`
- PDF header evidence: `%PDF-1.5`
- stdout evidence: `easy.pdfModuleSource=C:\Program Files\T-FLEX CAD 17\Program\PDFExport.dll`, `easy.pdfModuleLocalExists=True`, `easy.pdfExportResult=True`, `easy.pdfSaved=True`, `factory.pdfExport.saved=True`

Verified live DXF/DWG output on 2026-05-25:

- command: `python -m tflex_harness.cli create-document --payload artifacts/factory_payloads/phase6_drawing_acad_payload.json --timeout-sec 120`
- factory run: `artifacts/runs/20260525_193001_690605_document_factory`
- DXF export run: `artifacts/runs/20260525_193003_794702_factory_dxf_export`
- DWG export run: `artifacts/runs/20260525_193005_958846_factory_dwg_export`
- DXF output: `artifacts/outputs/phase6_drawing_acad_export.dxf`, size `125193`, header `SECTION` / `$ACADVER` / `AC1027`
- DWG output: `artifacts/outputs/phase6_drawing_acad_export.dwg`, size `18220`, header bytes `41 43 31 30 32 37` (`AC1027`)
- stdout evidence: `easy.dxfExportResult=True`, `easy.dxfSaved=True`, `factory.dxfExport.saved=True`, `easy.dwgExportResult=True`, `easy.dwgSaved=True`, `factory.dwgExport.saved=True`

Verified live multi-step factory payload on 2026-05-25:

- command: `python -m tflex_harness.cli create-document --payload artifacts/factory_payloads/phase6_multi_step_payload.json --timeout-sec 120`
- factory run directory: `artifacts/runs/20260525_183813_757471_document_factory`
- generated snippet: `artifacts/runs/20260525_183813_757471_document_factory/factory_snippet.cs`
- snippet run directory: `artifacts/runs/20260525_183813_840239_factory_multi_step`
- source prototype: `C:\Program Files\T-FLEX CAD 17\Program\Прототипы\Электротехника\Клеммник.grb`
- verified stdout: `documentProperty.after.Title=Harness Multi Step Test`, `visibleText.line.after=Harness Circuit Multi`, `factory.allSet=True`, `document.saved=True`, `factory.property.0=Harness Multi Step Test`, `factory.visibleText.oldAfter.1=0`, `factory.visibleText.newAfter.1=1`, `factory.allValid=True`

Verified live factory sample matrix on 2026-05-25:

- command: `python -m tflex_harness.cli document-factory-samples --timeout-sec 120 --output-dir artifacts/document_factory_validation/live_samples_20260525_fix`
- matrix: `artifacts/document_factory_validation/live_samples_20260525_fix/document_factory_samples_matrix.json`
- csv: `artifacts/document_factory_validation/live_samples_20260525_fix/document_factory_samples_matrix.csv`
- summary: `selected=4`, `attempted=4`, `passed=4`, `failed=0`
- covered categories: `3d_part`, `drawing`, `specification`, `table`
- output files: `factory_3d_part.grb` size `28542`, `factory_drawing.grb` size `25465`, `factory_specification.grb` size `29101`, `factory_table.grb` size `63297`

Updated matrix with STEP requested for the 3D sample:

- command: `python -m tflex_harness.cli document-factory-samples --timeout-sec 120 --output-dir artifacts/document_factory_validation/live_samples_step_20260525`
- matrix: `artifacts/document_factory_validation/live_samples_step_20260525/document_factory_samples_matrix.json`
- summary: `selected=4`, `attempted=4`, `passed=4`, `failed=0`
- 3D row output formats: `grb`, `step`
- 3D row STEP output: `factory_3d_part.step`, size `316`

Updated matrix with PDF requested for the drawing sample:

- command: `python -m tflex_harness.cli document-factory-samples --timeout-sec 120 --output-dir artifacts/document_factory_validation/live_samples_pdf_20260525`
- matrix: `artifacts/document_factory_validation/live_samples_pdf_20260525/document_factory_samples_matrix.json`
- summary: `selected=4`, `attempted=4`, `passed=4`, `failed=0`
- drawing row output formats: `grb`, `pdf`
- drawing row PDF output: `factory_drawing.pdf`, size `11109`

Updated matrix with PDF+DXF+DWG requested for the drawing sample:

- command: `python -m tflex_harness.cli document-factory-samples --timeout-sec 120 --output-dir artifacts/document_factory_validation/live_samples_acad_20260525`
- matrix: `artifacts/document_factory_validation/live_samples_acad_20260525/document_factory_samples_matrix.json`
- csv: `artifacts/document_factory_validation/live_samples_acad_20260525/document_factory_samples_matrix.csv`
- summary: `selected=4`, `attempted=4`, `passed=4`, `failed=0`
- drawing row output formats: `grb`, `pdf`, `dxf`, `dwg`
- drawing row outputs: `factory_drawing.pdf` size `11109`, `factory_drawing.dxf` size `125189`, `factory_drawing.dwg` size `18220`

Verified live open-only audit batch on 2026-05-25:

- command: `python -m tflex_harness.cli document-factory-batch --payload-dir artifacts/factory_payloads --glob phase6_property_payload.json --audit-open-only --timeout-sec 120 --output-dir artifacts/document_factory_batches/live_audit_open_only_20260525`
- matrix: `artifacts/document_factory_batches/live_audit_open_only_20260525/document_factory_batch_matrix.json`
- summary: `selected=1`, `attempted=1`, `passed=1`, `failed=0`
- audit run: `artifacts/runs/20260525_195835_783892_prototype_metadata`
- row evidence: `stage=audit`, `audit_open_only=True`, `output_formats=[]`, `variables=47`, `pages=1`
