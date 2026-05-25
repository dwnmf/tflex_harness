from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any


def load_evidence(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def write_semantic_outputs(evidence_path: str | Path, output_dir: str | Path) -> dict[str, Any]:
    evidence = load_evidence(evidence_path)
    semantic = recognize_semantic_model(evidence)
    code = emit_parametric_csharp(semantic)
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    semantic_path = out / "semantic_model.json"
    code_path = out / "parametric_candidate.cs"
    semantic_path.write_text(json.dumps(semantic, ensure_ascii=False, indent=2), encoding="utf-8")
    code_path.write_text(code, encoding="utf-8")
    return {
        "ok": True,
        "evidence_path": str(Path(evidence_path)),
        "output_dir": str(out),
        "semantic_path": str(semantic_path),
        "code_path": str(code_path),
        "recognized_count": len([item for item in semantic["operations"] if item["kind"] != "raw_polyline_extrusion"]),
        "operation_count": len(semantic["operations"]),
    }


def recognize_semantic_model(evidence: dict[str, Any]) -> dict[str, Any]:
    operations = [recognize_operation(op) for op in evidence.get("operations", [])]
    return {
        "source_grb": evidence.get("source_grb"),
        "operation_count": evidence.get("operation_count", len(operations)),
        "recognizer": "tflex_harness.grb_reverse.v1",
        "operations": operations,
    }


def recognize_operation(op: dict[str, Any]) -> dict[str, Any]:
    name = str(op.get("name", "operation"))
    center = _bbox_center(op)
    z_min = float(op.get("z_min_mm", _bbox_min(op)[2]))
    height = float(op.get("height_mm", _bbox_span(op)[2]))
    contours = op.get("contours", [])

    base: dict[str, Any] = {
        "source_index": op.get("index"),
        "source_name": name,
        "z_min_mm": _round(z_min),
        "height_mm": _round(height),
        "center_mm": [_round(center[0]), _round(center[1])],
    }

    if len(contours) >= 2 and _is_circle_contour(contours[0], (center[0], center[1])):
        inner_stats = _radius_clusters(contours[-1], (center[0], center[1]))
        teeth = _gear_tooth_count(contours[-1], (center[0], center[1]), high=False)
        if teeth >= 3 and len(inner_stats) >= 2:
            outer = _diameter_from_contour(contours[0], (center[0], center[1]))
            root = 2.0 * inner_stats[-1]
            tip = 2.0 * inner_stats[0]
            base.update({
                "kind": "internal_trapezoid_gear_ring",
                "confidence": 0.95,
                "teeth": teeth,
                "outer_dia_mm": _round(outer),
                "internal_root_dia_mm": _round(root),
                "tooth_tip_dia_mm": _round(tip),
                "phase_deg": _round(_estimate_internal_phase_deg(contours[-1], (center[0], center[1]))),
                "tooth_style": "clearanced",
            })
            return base

    if contours:
        gear = contours[0]
        radii = _radius_clusters(gear, (center[0], center[1]))
        teeth = _gear_tooth_count(gear, (center[0], center[1]), high=True)
        if teeth >= 3 and len(radii) >= 2:
            root = 2.0 * radii[0]
            outer = 2.0 * radii[-1]
            bore = None
            if len(contours) > 1 and _is_circle_contour(contours[1], (center[0], center[1])):
                bore = _diameter_from_contour(contours[1], (center[0], center[1]))
            base.update({
                "kind": "external_trapezoid_gear_with_bore" if bore else "external_trapezoid_gear",
                "confidence": 0.95,
                "teeth": teeth,
                "root_dia_mm": _round(root),
                "outer_dia_mm": _round(outer),
                "phase_deg": _round(_estimate_external_phase_deg(gear, (center[0], center[1]))),
                "tooth_style": "clearanced",
            })
            if bore is not None:
                base["bore_dia_mm"] = _round(bore)
            return base

    if len(contours) == 2 and _is_circle_contour(contours[0], (center[0], center[1])) and _is_circle_contour(contours[1], (center[0], center[1])):
        outer = _diameter_from_contour(contours[0], (center[0], center[1]))
        inner = _diameter_from_contour(contours[1], (center[0], center[1]))
        base.update({
            "kind": "ring_extrusion",
            "confidence": 0.9,
            "outer_dia_mm": _round(outer),
            "inner_dia_mm": _round(inner),
            "outer_segments": len(_contour_points(contours[0])),
            "inner_segments": len(_contour_points(contours[1])),
        })
        return base

    if len(contours) == 1 and _is_circle_contour(contours[0], (center[0], center[1])):
        diameter = _diameter_from_contour(contours[0], (center[0], center[1]))
        base.update({
            "kind": "circle_extrusion",
            "confidence": 0.94,
            "diameter_mm": _round(diameter),
            "segments": len(_contour_points(contours[0])),
        })
        return base

    if len(contours) >= 2 and _is_circle_contour(contours[0], (center[0], center[1])):
        outer = _diameter_from_contour(contours[0], (center[0], center[1]))
        inner_stats = _radius_clusters(contours[-1], (center[0], center[1]))
        root = 2.0 * inner_stats[-1]
        tip = 2.0 * inner_stats[0]
        base.update({
            "kind": "unrecognized_internal_profile_ring",
            "confidence": 0.45,
            "outer_dia_mm": _round(outer),
            "internal_root_dia_mm": _round(root),
            "tooth_tip_dia_mm": _round(tip),
            "contour_count": len(contours),
        })
        return base

    base.update({
        "kind": "raw_polyline_extrusion",
        "confidence": 0.2,
        "contour_count": len(contours),
    })
    return base


def emit_parametric_csharp(semantic: dict[str, Any]) -> str:
    lines: list[str] = [
        "using System;",
        "using TFlex.Model;",
        "using TFlex.Model.Model3D;",
        "using TFlexEasy;",
        "",
        "public class Program {",
        "  public static int Main(){",
        "    using (var sess = EasySession.Start3D()) {",
        "      var doc = sess.New3DDocument(false);",
        "      doc.BeginChanges(\"parametric reconstruction from semantic model\");",
        "      EasyGearToothStyle style = EasyGearToothStyle.Clearanced;",
        "",
    ]
    for idx, op in enumerate(semantic.get("operations", [])):
        profile = f"p{idx}"
        name = _cs_string(str(op["source_name"]) + "_parametric")
        profile_name = _cs_string(str(op["source_name"]) + "_profile_parametric")
        kind = op["kind"]
        cx, cy = op["center_mm"]
        if kind == "external_trapezoid_gear_with_bore":
            lines.append(
                f"      var {profile} = EasyGears.ExternalTrapezoidGearWithBoreAt(doc, {_cs_num(cx)}, {_cs_num(cy)}, {op['teeth']}, {_cs_num(op['root_dia_mm'])}, {_cs_num(op['outer_dia_mm'])}, {_cs_num(op['bore_dia_mm'])}, {_cs_num(op['phase_deg'])}, style, {profile_name});"
            )
        elif kind == "external_trapezoid_gear":
            lines.append(
                f"      var {profile} = EasyGears.ExternalTrapezoidGearAt(doc, {_cs_num(cx)}, {_cs_num(cy)}, {op['teeth']}, {_cs_num(op['root_dia_mm'])}, {_cs_num(op['outer_dia_mm'])}, {_cs_num(op['phase_deg'])}, style, {profile_name});"
            )
        elif kind == "internal_trapezoid_gear_ring":
            lines.append(
                f"      var {profile} = EasyGears.InternalTrapezoidGearRingAt(doc, {_cs_num(cx)}, {_cs_num(cy)}, {op['teeth']}, {_cs_num(op['outer_dia_mm'])}, {_cs_num(op['internal_root_dia_mm'])}, {_cs_num(op['tooth_tip_dia_mm'])}, {_cs_num(op['phase_deg'])}, style, {profile_name});"
            )
        elif kind == "circle_extrusion":
            segments = int(op.get("segments") or 96)
            lines.append(
                f"      var {profile} = EasyGears.CircleAt(doc, {_cs_num(cx)}, {_cs_num(cy)}, {_cs_num(op['diameter_mm'])}, {segments}, {profile_name});"
            )
        elif kind == "ring_extrusion":
            lines.append(
                f"      var {profile} = EasyProfiles.Ring(doc, {_cs_num(op['outer_dia_mm'])}, {_cs_num(op['inner_dia_mm'])}, {profile_name});"
            )
        else:
            lines.append(f"      // Unsupported semantic kind for {name}: {kind}. Use raw contour reconstruction fallback.")
            continue
        lines.append(
            f"      EasySolids.ExtrudeMm(doc, {profile}, {_cs_num(op['z_min_mm'])}, {_cs_num(op['height_mm'])}, {name});"
        )
        lines.append("")
    lines.extend([
        "      var end = doc.EndChanges();",
        "      EasyDiagnostics.Print(\"endChanges\", end);",
        "      if (end.ToString() != \"OK\") return 10;",
        "      var operations = Document3D.GetOperations(doc);",
        "      EasyDiagnostics.Print(\"operations\", operations.Count);",
        "      foreach (Operation op in operations) EasyDiagnostics.PrintBodyBoxMm(op.Name, op);",
        "      bool grb = EasyExport.Grb(doc, sess.ArtifactPath(\"parametric_from_grb.grb\"));",
        "      EasyDiagnostics.Print(\"grbSaved\", grb);",
        "      bool step = EasyExport.Step(doc, sess.ArtifactPath(\"parametric_from_grb.step\"));",
        "      return (grb && step) ? 0 : 20;",
        "    }",
        "  }",
        "}",
        "",
    ])
    return "\n".join(lines)


def _bbox_min(op: dict[str, Any]) -> list[float]:
    return [float(v) for v in op.get("bbox", {}).get("min", [0, 0, 0])]


def _bbox_span(op: dict[str, Any]) -> list[float]:
    return [float(v) for v in op.get("bbox", {}).get("span", [0, 0, 0])]


def _bbox_center(op: dict[str, Any]) -> tuple[float, float, float]:
    mins = _bbox_min(op)
    spans = _bbox_span(op)
    return mins[0] + spans[0] / 2.0, mins[1] + spans[1] / 2.0, mins[2] + spans[2] / 2.0


def _contour_points(contour: dict[str, Any]) -> list[tuple[float, float]]:
    points = [(float(x), float(y)) for x, y in contour.get("points", [])]
    if len(points) > 1 and _distance(points[0], points[-1]) < 1e-7:
        return points[:-1]
    return points


def _diameter_from_contour(contour: dict[str, Any], center: tuple[float, float]) -> float:
    radii = [_distance(point, center) for point in _contour_points(contour)]
    return 2.0 * max(radii) if radii else 0.0


def _is_circle_contour(contour: dict[str, Any], center: tuple[float, float], tolerance_mm: float = 0.05) -> bool:
    radii = [_distance(point, center) for point in _contour_points(contour)]
    if len(radii) < 8:
        return False
    return max(radii) - min(radii) <= tolerance_mm


def _radius_clusters(contour: dict[str, Any], center: tuple[float, float]) -> list[float]:
    radii = sorted(_distance(point, center) for point in _contour_points(contour))
    if not radii:
        return [0.0]
    clusters: list[list[float]] = []
    for radius in radii:
        if not clusters or abs(radius - (sum(clusters[-1]) / len(clusters[-1]))) > 0.5:
            clusters.append([radius])
        else:
            clusters[-1].append(radius)
    return [sum(cluster) / len(cluster) for cluster in clusters]


def _gear_tooth_count(contour: dict[str, Any], center: tuple[float, float], high: bool) -> int:
    points = _contour_points(contour)
    if len(points) < 12:
        return 0
    radii = [_distance(point, center) for point in points]
    min_radius = min(radii)
    max_radius = max(radii)
    if max_radius - min_radius < 0.5:
        return 0
    threshold = (min_radius + max_radius) / 2.0
    flags = [radius > threshold if high else radius < threshold for radius in radii]
    return len(_true_runs_circular(points, flags))


def _true_runs_circular(points: list[tuple[float, float]], flags: list[bool]) -> list[list[tuple[float, float]]]:
    if not points or not any(flags):
        return []
    count = len(points)
    starts = [i for i in range(count) if flags[i] and not flags[(i - 1) % count]]
    if not starts and all(flags):
        return [points]
    runs: list[list[tuple[float, float]]] = []
    for start in starts:
        run: list[tuple[float, float]] = []
        i = start
        while flags[i]:
            run.append(points[i])
            i = (i + 1) % count
            if i == start:
                break
        runs.append(run)
    return runs


def _estimate_external_phase_deg(contour: dict[str, Any], center: tuple[float, float]) -> float:
    points = _contour_points(contour)
    if len(points) < 4:
        return 0.0
    radii = [_distance(point, center) for point in points]
    threshold = (min(radii) + max(radii)) / 2.0
    runs = _true_runs_circular(points, [radius > threshold for radius in radii])
    if runs:
        return _run_center_angle_deg(runs[0], center)
    return _angle_deg(points[0], center)


def _estimate_internal_phase_deg(contour: dict[str, Any], center: tuple[float, float]) -> float:
    points = _contour_points(contour)
    if len(points) < 4:
        return 0.0
    radii = [_distance(point, center) for point in points]
    threshold = (min(radii) + max(radii)) / 2.0
    runs = _true_runs_circular(points, [radius < threshold for radius in radii])
    if runs:
        return _run_center_angle_deg(runs[0], center)
    return _angle_deg(points[0], center)


def _run_center_angle_deg(run: list[tuple[float, float]], center: tuple[float, float]) -> float:
    x = 0.0
    y = 0.0
    for point in run:
        angle = math.radians(_angle_deg(point, center))
        x += math.cos(angle)
        y += math.sin(angle)
    return _normalize_deg(math.degrees(math.atan2(y, x)))


def _angle_deg(point: tuple[float, float], center: tuple[float, float]) -> float:
    return _normalize_deg(math.degrees(math.atan2(point[1] - center[1], point[0] - center[0])))


def _normalize_deg(angle: float) -> float:
    while angle <= -180.0:
        angle += 360.0
    while angle > 180.0:
        angle -= 360.0
    return angle


def _distance(a: tuple[float, float], b: tuple[float, float]) -> float:
    return math.hypot(a[0] - b[0], a[1] - b[1])


def _round(value: float) -> float:
    rounded = round(float(value), 8)
    nearest_int = round(rounded)
    if abs(rounded - nearest_int) < 1e-6:
        return float(nearest_int)
    return rounded


def _cs_string(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def _cs_num(value: float | int) -> str:
    return f"{float(value):.8f}".rstrip("0").rstrip(".") or "0"
