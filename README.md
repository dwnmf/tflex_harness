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

The MCP server entrypoint is `tflex-harness-mcp` and maps to `tflex_harness.mcp_server:main`.

Recipe `output_file` arguments are intentionally constrained to `artifacts/tflex_docs/...`; the harness rejects paths outside that tree so live runs do not write random files into the repository or user folders.

Snippet runs receive:

- `TFLEX_HARNESS_RUN_DIR` — per-run artifact root.
- `TFLEX_HARNESS_ARTIFACTS_DIR` — writable folder for snippet-generated files.

`result.json` includes `build_log`, `stdout_path`, `stderr_path`, `run_log`, `artifacts_dir`, and discovered files under `artifacts/`.
Timeouts are structured as `stage: "timeout"` with `phase: "compile"` or `phase: "run"`.
Each `run-csharp` / `run_csharp_tflex` call also appends a compact event to `logs/events.jsonl` with stage, phase, run directory, cache info, diagnostic count, and artifact count.

## Verified recipes

- `environment_probe` — initializes and exits a minimal read-only API session.
- `create_empty_document` — creates an invisible empty 2D document, saves it as `.grb`, closes it, and exits the session.
- `save_document_as_temp` — creates a hidden temporary 2D document, verifies `SaveAs` to a `.grb` artifact path, writes a snippet artifact marker, closes the document, and exits the session.
- `create_simple_2d_line` — creates two free 2D nodes, a construction line through them, verifies `Get2DObjects()` count/types, saves `.grb`, closes the document, and exits the session.
- `create_simple_3d_extrusion` — creates a hidden 3D document, builds a circular area profile on a standard workplane, verifies one `ThickenExtrusion` operation with non-null body/geometry and positive bounding box, saves `.grb`, closes the document, and exits the session.
