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
- `python -m tflex_harness.cli prototypes-metadata` — opens copied `.grb` prototypes and extracts document/page/2D/3D/variable/fragment metadata into JSON/CSV indexes.

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
