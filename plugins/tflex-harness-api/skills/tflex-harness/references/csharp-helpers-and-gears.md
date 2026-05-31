# C# Helpers and Gear Rules

## Contents
- Helper source policy
- Known helper sets
- Gear assembly rules

## C# Helper Source Policy

Use helper `.cs` files when they prevent repeated T-FLEX API mistakes. They are source files compiled with the visible snippet, not a hidden wrapper DLL.

Known helper sets:

- `easy_core`: `TFlexEasyUnits.cs`, `TFlexEasyDiagnostics.cs`
- `easy_session`: core plus `TFlexEasySession.cs`
- `easy_3d`: session/profile/gear/solid/placement helpers
- `easy_gears`: `TFlexEasyGears.cs` plus minimal dependencies
- `easy_export`: session/export helpers
- `easy_prototype`: installed `.grb` prototype copy/open/save helpers
- `easy_variables`: prototype/session helpers plus text/real variable mutation helpers
- `easy_text`: prototype/session helpers plus `RichText` table cell, visible 2D text replacement helpers, and first visible non-table text helpers
- `easy_specification`: prototype/session helpers plus `BOMObject` first-record standard field helpers for specification prototypes
- `easy_document_properties`: prototype/session helpers plus writable `Document.Properties` string mutation helpers
- `easy_assembly_validation`: session/prototype/diagnostics helpers plus AABB broad phase, exact `BaseBody.Clash(...)`, `Fragment3D` floating checks, DOF-lite counting, and `Document3D.GetMates(doc)` mate inspection
- `all`: every helper source

For gear assemblies:

1. Prefer `TFlexEasyGears.cs` direct-XY profile helpers:
   - `EasyGears.ExternalTrapezoidGearAt(...)`
   - `EasyGears.ExternalTrapezoidGearWithBoreAt(...)`
   - `EasyGears.InternalTrapezoidGearRingAt(...)`
   - `EasyGears.CircleAt(...)`
2. Do not build centered gear profiles and then rely on body `MoveMm` unless the task specifically needs transformed bodies.
3. Use explicit tooth phase helpers:
   - `EasyGears.PhaseForGapAtAxisDeg(teeth, axisDeg)`
   - `EasyGears.PhaseForToothAtAxisDeg(teeth, axisDeg)`
   - `EasyGears.PlanetToothFacingSunPhaseDeg(planetAxisDeg)`
4. For simplified trapezoid gear visuals, start with `EasyGearToothStyle.Clearanced`; use `Wide` only if the user wants chunky schematic teeth.
5. Print mesh evidence with radial clearances and planet center radii. BBox alone is not enough for gear mesh quality.
