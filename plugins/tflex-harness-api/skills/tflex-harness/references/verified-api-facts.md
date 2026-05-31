# Verified API Facts

## Contents
- Export API facts
- Variables and expressions
- Primitive solids
- Transformations
- System commands

## Verified Export API Facts

Verified locally in T-FLEX CAD 17 on 2026-05-25.

- `EasyExport.Grb(doc, path)` wraps `Document.SaveAs(path)`.
- `EasyExport.Step(doc, path)` wraps `Document.ExportToSTEP.Export(path)`.
- `EasyExport.Dxf(doc, path)` wraps `Document.ExportToDXF.Export(path)`.
- `EasyExport.Dwg(doc, path)` wraps `Document.ExportToDWG.Export(path)`.
- `ExportToSTEP.Export(...)` can return `False` while still writing a valid non-empty STEP. Treat non-empty file artifact as success unless newer live evidence contradicts this.
- 2D PDF uses `new TFlex.Model.ExportToPDF(document)`, not `Document.ExportToPDF`; `Document.ExportToPDF` does not compile in T-FLEX CAD 17.
- For headless PDF export, set `OpenExportFile=false` and `IsSelectPagesDialogEnabled=false`.
- Live PDF export failed with `Error loading module PDFExport.dll` until `PDFExport.dll` was copied from `<tflex-program>` to the snippet current directory. `EasyExport.Pdf(...)` now performs this copy by searching `PATH`.
- Live DXF/DWG drawing export succeeded with `easy.dxfExportResult=True`, `easy.dxfSaved=True`, `easy.dwgExportResult=True`, and `easy.dwgSaved=True`. DXF header evidence: `SECTION`, `$ACADVER`, `AC1027`; DWG header bytes: `41 43 31 30 32 37` (`AC1027`).

## Verified 3D API Facts

Verified locally in T-FLEX CAD 17 on 2026-05-22.

### Variables and expressions

- Create `Variable` objects in their own `doc.BeginChanges(...)` / `doc.EndChanges()` block before geometry that references them.
- Mixing variable creation and dependent 3D operations in one changes block can yield `CompleteError` and disposed-object errors.
- T-FLEX variable trigonometry uses degrees for `sin(Angle)` and `cos(Angle)`. Do not convert `Angle` to radians unless new live evidence says otherwise.

### Primitive solids

- For simple parametric solids, prefer `TFlex.Model.Model3D.Block` and `TFlex.Model.Model3D.Cylinder`.
- `Cylinder` uses `Diameter` and `Height`, not `Radius`.
- `Cylinder.Geometry.Axis` can be non-null after successful `EndChanges()`.
- `Cylinder.Geometry.Surface` was null in simple primitive probes. Do not assume it exists for tangency mates.
- `Block.Geometry.Plane` can be non-null after successful `EndChanges()`.

### Transformations

Use `Object3D.Transformations.AddBaseTransfGroup()` with:

- `TransformationGroup.AddMoveTransf(TransformationCoordinate.X/Y/Z, Parameter)`
- `TransformationGroup.AddRotateTransf(TransformationCoordinate.X/Y/Z, Parameter)`

Do not use `Object3D.VolatileTransformations` in new snippets. Live T-FLEX CAD 17 can throw: `Property VolatileTransformation is obsolete. Use Transformations property instead`.

When combining primitive axis rotation and world placement through separate base transformation groups, add the move group before the rotate group. Live recipe `artifacts/runs/20260527_113601_563578_recipe_helper_solid_primitives_backlog` proved that `CylinderMm(... axis X/Y/Z ...)` then lands at the requested world bbox center. The opposite order rotated the translation vector.

For flat gear profiles, prefer direct XY profile coordinates from `TFlexEasyGears.cs` over body transforms. Live evidence on 2026-05-25 showed direct-XY planetary gears reopened from `.grb` with three planets still at R42; transformed-centered gear bodies were visually confusing in CAD inspection.

### System commands

- `TFLEX_PROGRAM_DIR\CommandInfo` can be used as a local command-name discovery source; live recipe `artifacts/runs/20260527_121244_863443_recipe_helper_command_probe_backlog` found 195 entries and `CreateMate`.
- `Application.RunSystemCommand("ZoomMax", new ModelObject[0], callback)` started successfully in a harness EXE session. This proves `EasyCommandProbe.TryRunSystemCommand(...)` works for at least one real command name.
- `ZoomMax` works even though `C:\Program Files\T-FLEX CAD 17\Program\CommandInfo\ZoomMax.txt` does not exist. Do not treat `CommandInfo` stems as a full/authoritative command registry.
- `RunSystemCommand("CreateMate", new ModelObject[0], callback)` returned `InvalidOperationException: Specified command not found` in the same recipe. Do not assume every `CommandInfo` file stem is directly accepted by `RunSystemCommand`.
- Brute-force matrix run `artifacts/runs/20260527_122936_620643_mate_command_bf_matrix` tested `CreateMate`, `Create Mate`, `<3CT>`, `3CT`, `MoveMatedComponents`, `DocumentMoveAssembly`, `ReferToAssemblyGeometry` across part+assembly, hidden+visible, and fragment selection variants; all returned `Specified command not found`. Only `ZoomMax` started.
- In the same matrix, passing selected fragment objects made `ZoomMax` fail with `InvalidOperationException: No Active Document`.
- Active-document probe `artifacts/runs/20260527_123218_336535_active_document_easy_session_probe` showed `Document.Visible=True` but `Document.IsUIVisible=False`, with `Application.ActiveDocument==null` and `Application.ActiveViewDocument==null` even after `Document.Activate()`.
- Macro-enabled run `artifacts/runs/20260527_123104_865470_mate_command_macro_activation_probe` still rejected `CreateMate`; separate probe `artifacts/runs/20260527_123203_607442_active_document_probe_with_helpers` failed on `EnableMacros=true` with `FileNotFoundException: TFlexMacroLoader`.
- Reflection run `artifacts/runs/20260527_123615_622023_session_setup_reflection_probe` showed `ApplicationSessionSetup` has no UI-show/activate options; documents in harness session had `Views` count `0`.
- Probe `artifacts/runs/20260527_123637_919504_open3dview_active_probe` showed `Document.Open3DView()` returned `null`; it did not create active view/document context.
- Ribbon probe `artifacts/runs/20260527_123907_832196_ribbon_tabs_probe` showed `RibbonBar.TabCount=0` and empty tabs collection in harness session.
- `MainWindow.ProcessCommand(Int32)` exists, but scan `artifacts/runs/20260527_124022_577725_processcommand_scan_0_400` returned no `true` IDs in that range.
