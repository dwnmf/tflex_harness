# Recipe: environment_probe

Status: verified live on this machine.

## Purpose

Verify that an external C# EXE can initialize and exit a T-FLEX CAD 17 Open API session using the real `TFlexAPI.dll`.

## Documentation Evidence

From `D:\REALPROJECTS\tflex_api\llm\symbols.jsonl`:

- `M:TFlex.Application.InitSession(TFlex.ApplicationSessionSetup)` — initializes API for external EXE usage and returns `true` on success.
- `M:TFlex.Application.ExitSession` — exits API session and is paired with `InitSession`.
- `P:TFlex.Application.IsSessionInitialized` — session initialization state.
- `T:TFlex.ApplicationSessionSetup` — external OpenAPI session setup.
- `P:TFlex.ApplicationSessionSetup.ReadOnly` — read-only mode.
- `P:TFlex.ApplicationSessionSetup.Enable3D` — load 3D module.
- `P:TFlex.ApplicationSessionSetup.EnableDOCs` — enable DOCs integration.
- `P:TFlex.ApplicationSessionSetup.EnableMacros` — enable macros.
- `P:TFlex.ApplicationSessionSetup.PromptToSaveModifiedDocuments` — save prompt behavior.
- `P:TFlex.ApplicationSessionSetup.ProtectionLicense` and `F:TFlex.ApplicationSessionSetup.License.TFlexAPI` — license selection.

## C# Snippet

```csharp
using System;
using TFlex;
public class Program {
  public static int Main(){
    var setup = new ApplicationSessionSetup();
    setup.ReadOnly = true;
    setup.Enable3D = false;
    setup.EnableDOCs = false;
    setup.EnableMacros = false;
    setup.PromptToSaveModifiedDocuments = false;
    setup.ProtectionLicense = ApplicationSessionSetup.License.TFlexAPI;
    Console.WriteLine("before=" + Application.IsSessionInitialized);
    bool ok = Application.InitSession(setup);
    Console.WriteLine("init=" + ok);
    Console.WriteLine("after=" + Application.IsSessionInitialized);
    if (Application.IsSessionInitialized) Application.ExitSession();
    Console.WriteLine("exited=" + Application.IsSessionInitialized);
    return ok ? 0 : 3;
  }
}
```

## Verification

Test:

```powershell
python -m pytest tests/integration/test_tflex_live_session.py -v
```

Observed evidence:

```text
before=False
init=True
after=True
exited=False
```

## Assumptions

- T-FLEX CAD 17 is installed at `C:\Program Files\T-FLEX CAD 17`.
- `PATH` is prefixed with `C:\Program Files\T-FLEX CAD 17\Program` when running snippets so native dependencies are found.
- The `TFlexAPI` license mode is available in this environment.

## Limitations

- This recipe verifies session initialization only.
- It does not create, edit, save, or close user documents.
- It intentionally disables 3D, DOCs integration, and macros for a minimal live probe.
