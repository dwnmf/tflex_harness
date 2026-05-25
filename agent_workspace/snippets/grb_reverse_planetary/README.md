# GRB reverse planetary prototype

Input GRB: `D:\REALPROJECTS\tflex_harness\artifacts\runs\20260525_124700_025877_recipe_helper_planetary_static_assembly\artifacts\helper_planetary_static_assembly.grb`

## What worked

This prototype proves a practical geometry-level loop:

1. Open `.grb` read-only with `Application.OpenDocument(path, false, true)`.
2. Read `Document3D.GetOperations(doc)`.
3. For each `ThickenExtrusion`, get:
   - operation name/type;
   - bbox in mm;
   - `ForwardLength.Value`/height evidence;
   - `AreaProfile.Area` through the extrusion profile owner;
   - each `Area` contour segment;
   - `OutlineContourSegment.Direction`;
   - `PolylineGeometry.Count`, `GetX(i)`, `GetY(i)`.
4. Emit `model_evidence_with_contours.json`.
5. Generate `reconstruct_candidate.cs` using those contours as visible C# source.
6. Run that candidate to create new `.grb` and STEP.

## Live evidence

- source contour evidence run: `artifacts/runs/20260525_131329_403568_grb_to_csharp_contour_evidence`
- reconstruction run: `artifacts/runs/20260525_131521_838617_grb_reverse_planetary_reconstruct_live`
- reconstructed evidence run: `artifacts/runs/20260525_131616_908440_grb_reverse_planetary_reconstructed_evidence`

Compare result:

- `operation_count_match=True`
- `max_bbox_delta_mm=1.000000082740371e-08`
- `contour_counts_match=True`
- `point_counts_match=True`

## Output files

- `reconstruct_candidate.cs` — generated C# reconstruction from saved GRB contours.
- `model_evidence_with_contours.json` — raw evidence used to generate the candidate.

Live reconstructed artifacts:

- `artifacts/runs/20260525_131521_838617_grb_reverse_planetary_reconstruct_live/artifacts/reconstructed_from_grb.grb`
- `artifacts/runs/20260525_131521_838617_grb_reverse_planetary_reconstruct_live/artifacts/reconstructed_from_grb.step`

## Limitation

This is not original design-intent decompilation. It recovers a visible C# geometry algorithm: profiles as polylines plus extrusion heights. It does not recover variables, constraints, formulas, feature history semantics, or true gear intent unless names/metadata reveal them.
