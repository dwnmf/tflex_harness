# T-FLEX Harness Goal

Date: 2026-05-25. Scope: helper-library implementation plan and progress tracker.

## Mission

Build **C# helper libraries for snippets** so agents can spend attention on engineering geometry, not repeated T-FLEX API ceremony.

Python remains the harness/control plane. C# remains the CAD execution boundary. The new helpers are C# source files compiled together with each visible snippet, not broad Python CAD tools.

## User Decision

The desired direction is explicit:

- create helper libraries;
- use them from snippets;
- reduce boilerplate around units, sessions, profiles, extrusion, placement, export, and diagnostics;
- keep evidence-driven compile/run/live validation.

This supersedes the previous “no helpers” planning stance in this file.

## Helper Model

Canonical helper source lives in:

```text
src/tflex_harness/csharp_helpers/
```

Initial files:

```text
src/tflex_harness/csharp_helpers/
  TFlexEasyUnits.cs
  TFlexEasySession.cs
  TFlexEasyProfiles.cs
  TFlexEasySolids.cs
  TFlexEasyPlacement.cs
  TFlexEasyExport.cs
  TFlexEasyDiagnostics.cs
```

Snippets use helpers like normal C#:

```csharp
using TFlexEasy;

public class Program {
  public static int Main() {
    using (var sess = EasySession.Start3D()) {
      var doc = sess.New3DDocument(visible: false);
      var profile = EasyProfiles.ExternalTrapezoidGear(doc, teeth: 24, rootDiaMm: 42, outerDiaMm: 54);
      var sun = EasySolids.ExtrudeMm(doc, profile, zMinMm: 0, heightMm: 8, name: "sun");
      EasyDiagnostics.PrintBodyBoxMm("sun", sun);
      return EasyExport.Step(doc, sess.ArtifactPath("planetary.step")) ? 0 : 20;
    }
  }
}
```

## Visibility Rule

Helpers are libraries, but not invisible magic.

For every run:

- helper `.cs` files are copied into the run directory;
- helper file paths and SHA256 hashes are written to `request.json` and `result.json`;
- `build.log` reflects compilation with snippet plus helper source files;
- source remains inspectable and editable in the repo;
- compile cache key includes helper content.

Default mode: compile helper **source** with the snippet.

Optional later mode: precompiled helper DLL only if source hash, version, and exact DLL evidence are persisted. Not first.

## Current Runner Gap

Current `SnippetRunner` writes and compiles one source file:

- run source: `snippet.cs`;
- cache source: `Snippet.cs`;
- compile command appends only that one source file.

Needed change:

- accept helper include names or helper set names;
- resolve helper source files;
- copy helper files to run dir;
- copy helper files to cache dir;
- compile all `.cs` files in one `csc.exe` invocation;
- include helper source content in cache key;
- persist helper metadata in result.

## Non-Goals

- Do not add public CAD-specific MCP tools like `create_gear` or `export_step`.
- Do not move CAD execution to Python/COM.
- Do not make long-lived T-FLEX sessions default.
- Do not hide helper source behind an unexplained binary.
- Do not claim helper correctness without compile and live evidence.

## Helper Quality Contract

Each helper method must have:

- clear C# signature;
- unit semantics in method name or XML/doc comment;
- narrow responsibility;
- no silent document saves outside artifact paths;
- no swallowed T-FLEX errors without diagnostic output;
- compile-only test snippet;
- live probe snippet when behavior touches T-FLEX runtime;
- stdout evidence for dimensions, paths, counts, and bbox when relevant.

## Initial Helper APIs

### `TFlexEasyUnits.cs`

Purpose: eliminate recurring unit mistakes.

Proposed API:

```csharp
namespace TFlexEasy {
  public static class EasyUnits {
    public static double MmToModel(double mm);
    public static double ModelToMm(double model);
    public static double DegToRad(double deg);
    public static string F(double value);
  }
}
```

Evidence needed:

- compile-only;
- live transform probe proving `AddMoveTransf` offsets behave as intended for mm-to-model conversion.

### `TFlexEasySession.cs`

Purpose: verified T-FLEX session lifecycle.

Proposed API:

```csharp
namespace TFlexEasy {
  public sealed class EasySession : System.IDisposable {
    public static EasySession Start3D();
    public static EasySession Start2D();
    public TFlex.Model.Document New3DDocument(bool visible);
    public TFlex.Model.Document New2DDocument(bool visible);
    public string ArtifactPath(string fileName);
    public void Dispose();
  }
}
```

Evidence needed:

- session init/exit stdout;
- close document in `Dispose`;
- no stale T-FLEX session after run.

### `TFlexEasyProfiles.cs`

Purpose: make profile creation deterministic.

Proposed API:

```csharp
namespace TFlexEasy {
  public static class EasyProfiles {
    public static TFlex.Model.Model3D.AreaProfile Circle(
      TFlex.Model.Document doc,
      double diameterMm,
      string name = "circle_profile");

    public static TFlex.Model.Model3D.AreaProfile Ring(
      TFlex.Model.Document doc,
      double outerDiaMm,
      double innerDiaMm,
      string name = "ring_profile");

    public static TFlex.Model.Model3D.AreaProfile ExternalTrapezoidGear(
      TFlex.Model.Document doc,
      int teeth,
      double rootDiaMm,
      double outerDiaMm,
      string name = "external_gear_profile");

    public static TFlex.Model.Model3D.AreaProfile InternalTrapezoidGearRing(
      TFlex.Model.Document doc,
      int teeth,
      double outerDiaMm,
      double internalRootDiaMm,
      double toothTipDiaMm,
      string name = "internal_gear_ring_profile");
  }
}
```

Evidence needed:

- generated tooth count;
- radial min/max from source points;
- bbox checks after extrusion.

### `TFlexEasySolids.cs`

Purpose: verified solid creation.

Proposed API:

```csharp
namespace TFlexEasy {
  public static class EasySolids {
    public static TFlex.Model.Model3D.ThickenExtrusion ExtrudeMm(
      TFlex.Model.Document doc,
      TFlex.Model.Model3D.AreaProfile profile,
      double zMinMm,
      double heightMm,
      string name);

    public static TFlex.Model.Model3D.Cylinder CylinderMm(
      TFlex.Model.Document doc,
      double diameterMm,
      double zMinMm,
      double heightMm,
      string name);
  }
}
```

Evidence needed:

- exact bbox Z span in mm;
- exact bbox X/Y for simple circle/cylinder;
- known `ThickenExtrusion` limitations documented.

### `TFlexEasyPlacement.cs`

Purpose: deterministic placement.

Proposed API:

```csharp
namespace TFlexEasy {
  public struct EasyPoint2 {
    public double XMm;
    public double YMm;
  }

  public static class EasyPlacement {
    public static EasyPoint2 PolarMm(double radiusMm, double angleDeg);
    public static void MoveMm(TFlex.Model.Model3D.Object3D obj, double xMm, double yMm, double zMm, string name = "move_mm");
    public static void RotateZDeg(TFlex.Model.Model3D.Object3D obj, double angleDeg, string name = "rotate_z_deg");
  }
}
```

Evidence needed:

- live bbox center shift check;
- degree/radian distinction documented.

### `TFlexEasyExport.cs`

Purpose: verified STEP export path.

Proposed API:

```csharp
namespace TFlexEasy {
  public static class EasyExport {
    public static bool Grb(TFlex.Model.Document doc, string path);
    public static bool Step(TFlex.Model.Document doc, string path);
  }
}
```

Evidence needed:

- `.grb` save evidence;
- `.step` or `.stp` export evidence;
- file exists and non-zero size;
- exact T-FLEX export API documented.

### `TFlexEasyDiagnostics.cs`

Purpose: standard stdout evidence and assertions.

Proposed API:

```csharp
namespace TFlexEasy {
  public static class EasyDiagnostics {
    public static void Print(string key, object value);
    public static BodyBoxMm PrintBodyBoxMm(string label, TFlex.Model.Model3D.Operation op);
    public static int FailIf(bool condition, int code, string message);
    public static bool Near(double actual, double expected, double tolerance);
  }

  public struct BodyBoxMm {
    public bool Valid;
    public double MinX, MinY, MinZ;
    public double MaxX, MaxY, MaxZ;
    public double SpanX, SpanY, SpanZ;
  }
}
```

Evidence needed:

- stdout shape stable;
- asserts return explicit exit codes;
- no exception masking.

## Runner Implementation Plan

### Iteration 1: Helper Source Discovery

Status: implemented.

Tasks:

- Add helper directory discovery under `src/tflex_harness/csharp_helpers`.
- Add allowlist of helper set names, for example `easy_core`, `easy_3d`, `easy_export`.
- Reject unknown helper names.
- Keep default behavior unchanged when no helpers requested.

Validation:

- unit test path resolution;
- unit test unknown helper rejection.

### Iteration 2: Compile Multiple Source Files

Status: implemented.

Tasks:

- Extend runner API with `helpers: list[str] | None`.
- Extend CLI with `--helper`.
- Extend MCP schema if needed.
- Copy selected helpers into run dir, e.g. `helpers/TFlexEasyUnits.cs`.
- Copy selected helpers into cache dir.
- Compile `Snippet.cs` plus helper `.cs` files.
- Include helper source content in compile cache key.

Validation:

- compile-only snippet using `using TFlexEasy;`;
- cache key changes when helper source changes;
- run dir includes helper source copies.

### Iteration 3: Metadata And Evidence

Status: implemented.

Tasks:

- Persist `helpers` in `request.json`.
- Persist `helper_sources` in `result.json`.
- Include helper path, copied path, SHA256, and size.
- Include helpers in event log summary.

Validation:

- unit tests for `result.json` shape;
- smoke compile-only run.

### Iteration 4: `TFlexEasyUnits` And `TFlexEasyDiagnostics`

Status: implemented and compile-verified.

Tasks:

- Implement no-CAD helper files first.
- Compile with trivial snippet.
- Add small tests.

Validation:

- compile-only pass;
- no live T-FLEX needed.

### Iteration 5: `TFlexEasySession`

Status: implemented and live-verified.

Tasks:

- Move known-good session pattern into source helper.
- Ensure `Dispose` closes document and exits session.
- Print explicit diagnostics.

Validation:

- live environment probe using helper;
- stdout contains init/exit evidence.

### Iteration 6: `TFlexEasyProfiles` And `TFlexEasyPlacement`

Status: implemented; profile compile verified, extrusion/profile path live-verified.

Tasks:

- Implement point generation and profile creation.
- Implement polar placement and transform helpers.
- Keep methods small and readable.

Validation:

- compile-only profile creation snippet;
- live bbox placement probe.

### Iteration 7: `TFlexEasySolids`

Status: implemented and live-verified for simple one-sided extrusion.

Tasks:

- Implement extrusion and cylinder creation.
- Probe `ThickenExtrusion` exact Z behavior.
- Adjust API if T-FLEX behavior differs from expectation.

Validation:

- live bbox Z checks;
- saved `.grb` evidence.

### Iteration 8: `TFlexEasyExport`

Status: implemented and live-verified for `.grb` and `.step` artifacts.

Tasks:

- Search local docs for exact STEP export API.
- Implement `.grb` first, STEP second.
- Print file evidence.

Validation:

- live STEP export probe;
- artifact file exists and non-zero size.

### Iteration 9: Planetary Gear Snippet Using Helpers

Status: implemented as snippet candidate and live-verified once.

Goal:

Build the prompt planetary assembly using helper libraries.

Snippet should be short and focused on the engineering spec:

- sun gear: 24 teeth, root 42, outside 54, bore 10;
- three planet gears: 18 teeth, root 31, outside 41, centers R42;
- ring: 60 internal teeth, outside 140, internal root 126, tooth-tip 114;
- carrier: circular plate Ø105, Z -5..-1;
- pins: three Ø6, height 14;
- gears: thickness 8;
- export STEP.

Validation:

- compile-only;
- live run;
- stdout expected-vs-actual checks;
- STEP artifact.

## Recipe Promotion Plan

Helpers themselves are not recipes. They are reusable C# source libraries.

Status: implemented for the four initial helper-backed recipes.

Promote helper-backed snippets to recipes when useful:

```text
agent_workspace/recipes/
  helper_environment_probe.cs
  helper_simple_extrusion.cs
  helper_step_export.cs
  helper_planetary_static_assembly.cs
```

Each recipe records:

- helper set used;
- helper hashes;
- live run dir;
- stdout evidence;
- artifact paths;
- limitations.

## Guardrails

- Helper source must stay small enough for agents to inspect.
- Prefer source inclusion over precompiled DLL.
- Do not silently change physical units.
- Every helper touching T-FLEX runtime gets live evidence.
- If helper behavior is uncertain, print uncertainty and fail contract checks.
- Do not use helpers to hide failed geometry checks.
- For flat gear assemblies, prefer `TFlexEasyGears.cs` direct-XY profile helpers and explicit tooth phase helpers over centered profiles plus body transforms.

## Immediate Next Commands

Use when implementation starts:

```powershell
rg -n "cache_key|Snippet.cs|cmd.append" src/tflex_harness/runner.py
python -m pytest tests/unit/test_runner_payloads.py -v
python -m tflex_harness.cli run-csharp --mode compile_only --code "public class Program { public static int Main(){ return 0; } }"
```

## Plan Iteration Log

- 2026-05-25: Replaced no-helper plan with explicit C# source helper library plan. Next target: helper source discovery and multi-source compile support in `SnippetRunner`.
- 2026-05-25: Implemented helper source discovery, multi-source compile, helper metadata, CLI/MCP `helpers`, recipe metadata passthrough, initial `TFlexEasy*` helper files, and README docs. Verified `easy_core` compile, all helpers compile, `EasySession` live, exact `ValueNo` extrusion bbox `20x20x8 mm`, and STEP export artifact `154986` bytes.
- 2026-05-25: Added `agent_workspace/snippets/helper_planetary_static_assembly/candidate.cs`. Live run `artifacts/runs/20260525_115830_457318_helper_planetary_static_live` passed with `operations=9`, contract checks `0`, and STEP artifact `helper_planetary_static_assembly.step` size `1530324` bytes.
- 2026-05-25: Promoted helper-backed recipes under `agent_workspace/recipes`: `helper_environment_probe`, `helper_simple_extrusion`, `helper_step_export`, and `helper_planetary_static_assembly`. `RecipeRegistry` reports all four `verified=True` and `freshness.status=fresh`.
- 2026-05-25: Live recipe runs passed: `artifacts/runs/20260525_120310_990914_recipe_helper_environment_probe`, `artifacts/runs/20260525_120312_702012_recipe_helper_simple_extrusion`, `artifacts/runs/20260525_120314_679135_recipe_helper_step_export`, and `artifacts/runs/20260525_120316_864653_recipe_helper_planetary_static_assembly`.
- 2026-05-25: Added live integration coverage in `tests/integration/test_tflex_helper_recipes.py`; all four helper recipe tests passed.
- 2026-05-25: Added `TFlexEasyGears.cs`, `easy_gears` helper set, clearanced direct-XY trapezoid gear profiles, explicit sun/ring/planet phase helpers, and radial clearance diagnostics. Updated `helper_planetary_static_assembly` to write both `.grb` and STEP. Live run `artifacts/runs/20260525_124302_419108_recipe_helper_planetary_static_assembly` passed with `operations=9`, `contractFailCode=0`, `mesh.sunRadialClearanceMm=0.5`, `mesh.ringRadialClearanceMm=0.5`, GRB size `617088`, and STEP size `1955262`.
