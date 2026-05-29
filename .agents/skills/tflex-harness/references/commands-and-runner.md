# Commands and C# Runner

## Contents
- Common commands
- Direct C# runner pattern
- Reference selection
- Artifact output rule
- Live session setup

## Common Commands

```powershell
python -m pytest tests/smoke -v
python -m tflex_harness.cli env
python -m tflex_harness.cli search "TFlex.Model.Document" --limit 5
python -m tflex_harness.cli recipes
python -m tflex_harness.cli state
python -m tflex_harness.cli run-csharp --mode compile_only --code "public class Program { public static int Main(){ return 0; } }"
python -m tflex_harness.cli prototypes-title-batch --timeout-sec 120 --fail-fast
python -m tflex_harness.cli prototypes-table-cell-batch --category Таблицы --timeout-sec 120 --fail-fast
python -m tflex_harness.cli prototypes-table-cell-batch --category Спецификации --timeout-sec 120
python -m tflex_harness.cli prototypes-specification-bom-field-batch --category Спецификации --timeout-sec 120
python -m tflex_harness.cli prototypes-first-visible-text-batch --category Электротехника --timeout-sec 120
python -m tflex_harness.cli document-factory-batch --payload-dir payloads --dry-run
python -m tflex_harness.cli document-factory-batch --failed-matrix artifacts/my_batch/document_factory_batch_matrix.json
python -m tflex_harness.cli document-factory-batch --payload-dir payloads --audit-open-only
tflex-harness-mcp
```

## Direct C# Runner Pattern

Use explicit references:

- `TFlexAPI` for application/session/document/2D API.
- `TFlexAPI3D` for 3D operations, geometry, fragments, mates.
- `TFlexCommandAPI` for command/UI API only.
- `TFlexAPIData` for data API only.

```powershell
$env:PYTHONPATH = Join-Path (Get-Location) 'src'
python -c "from tflex_harness.runner import run_csharp_snippet; result = run_csharp_snippet(code='public class Program { public static int Main(){ return 0; } }', mode='run', timeout_sec=30, references=[], artifact_prefix='manual_probe'); print(result)"
```

For snippet-generated outputs, write under `TFLEX_HARNESS_ARTIFACTS_DIR` / `EasySession.ArtifactPath(...)`. Do not write `.grb`/STEP files into random repo or user folders.

## Live Session Pattern

Known-good setup for writeable 3D live runs:

```csharp
var setup = new ApplicationSessionSetup();
setup.ReadOnly = false;
setup.Enable3D = true;
setup.EnableDOCs = false;
setup.EnableMacros = false;
setup.PromptToSaveModifiedDocuments = false;
setup.ProtectionLicense = ApplicationSessionSetup.License.TFlex3D;
bool init = Application.InitSession(setup);
```

Close documents and exit session in `finally`:

```csharp
try { if (document != null) document.Close(); } catch {}
if (Application.IsSessionInitialized) Application.ExitSession();
```
