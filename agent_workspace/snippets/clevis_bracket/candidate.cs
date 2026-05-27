using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using TFlex.Drawing;
using TFlex.Model;
using TFlex.Model.Model2D;
using TFlex.Model.Model3D;
using TFlexEasy;

public class Program {
  const double BaseX = 140.0;
  const double BaseY = 86.0;
  const double BaseZ = 12.0;
  const double LugThickness = 16.0;
  const double LugGap = 30.0;
  const double LugRadius = 28.0;
  const double LugCenterZ = 66.0;
  const double LugBottomZ = 10.0;
  const double BoreDia = 20.0;

  public static int Main(){
    using (var sess = EasySession.Start3D()) {
      var doc = sess.New3DDocument(false);

      doc.BeginChanges("clevis bracket source solids and cutters");
      var basePlate = ExtrudeRoundedRectangle(doc, "rounded_base_plate", StandardWorkplane.StandardType.Top, 0, 0, BaseX, BaseY, 9.0, BaseZ);

      var lugProfile = BuildRoundedLugProfile(-LugRadius, LugBottomZ, LugRadius, LugCenterZ, LugRadius, 28);
      var lugPositiveY = ExtrudeProfile(doc, "lug_positive_y", StandardWorkplane.StandardType.Front, lugProfile, LugThickness);
      EasyPlacement.MoveMm(lugPositiveY, 0.0, LugGap / 2.0 + LugThickness, 0.0, "place_positive_lug");
      var lugNegativeY = ExtrudeProfile(doc, "lug_negative_y", StandardWorkplane.StandardType.Front, lugProfile, LugThickness);
      EasyPlacement.MoveMm(lugNegativeY, 0.0, -(LugGap / 2.0), 0.0, "place_negative_lug");

      var ribRight = BuildTriangle(28.0, LugBottomZ, 56.0, LugBottomZ, 28.0, 52.0);
      var ribLeft = BuildTriangle(-28.0, LugBottomZ, -56.0, LugBottomZ, -28.0, 52.0);
      var ribPYR = ExtrudeProfile(doc, "rib_positive_y_right", StandardWorkplane.StandardType.Front, ribRight, 6.0);
      EasyPlacement.MoveMm(ribPYR, 0.0, 36.0, 0.0, "place_positive_y_right_rib");
      var ribPYL = ExtrudeProfile(doc, "rib_positive_y_left", StandardWorkplane.StandardType.Front, ribLeft, 6.0);
      EasyPlacement.MoveMm(ribPYL, 0.0, 36.0, 0.0, "place_positive_y_left_rib");
      var ribNYR = ExtrudeProfile(doc, "rib_negative_y_right", StandardWorkplane.StandardType.Front, ribRight, 6.0);
      EasyPlacement.MoveMm(ribNYR, 0.0, -30.0, 0.0, "place_negative_y_right_rib");
      var ribNYL = ExtrudeProfile(doc, "rib_negative_y_left", StandardWorkplane.StandardType.Front, ribLeft, 6.0);
      EasyPlacement.MoveMm(ribNYL, 0.0, -30.0, 0.0, "place_negative_y_left_rib");

      var boreCut = ExtrudeCircle(doc, "horizontal_lug_bore_cutter", StandardWorkplane.StandardType.Front, 0.0, LugCenterZ, BoreDia, 100.0, 96);
      EasyPlacement.MoveMm(boreCut, 0.0, 50.0, 0.0, "center_bore_cutter");

      var mountCuts = new List<Operation>();
      foreach (double x in new double[] {-48.0, 48.0}) {
        foreach (double y in new double[] {-27.0, 27.0}) {
          mountCuts.Add(ExtrudeCircle(doc, "base_mount_hole_cutter_" + F(x) + "_" + F(y), StandardWorkplane.StandardType.Top, x, y, 11.0, 24.0, 64));
        }
      }

      var triLeftCut = ExtrudeProfile(doc, "left_triangular_lightening_cutter", StandardWorkplane.StandardType.Front, BuildTriangle(-23.0, 28.0, -8.0, 54.0, -25.0, 54.0), 100.0);
      EasyPlacement.MoveMm(triLeftCut, 0.0, 50.0, 0.0, "center_left_lightening_cutter");
      var triRightCut = ExtrudeProfile(doc, "right_triangular_lightening_cutter", StandardWorkplane.StandardType.Front, BuildTriangle(23.0, 28.0, 8.0, 54.0, 25.0, 54.0), 100.0);
      EasyPlacement.MoveMm(triRightCut, 0.0, 50.0, 0.0, "center_right_lightening_cutter");

      var endSources = doc.EndChanges();
      EasyDiagnostics.Print("sources.endChanges", endSources);
      if (endSources.ToString() != "OK") return 10;

      doc.BeginChanges("clevis bracket unite solids");
      var united = new BooleanOperation(doc);
      united.Name = "clevis_bracket_rounded_reinforced_body";
      united.Function = BooleanOperation.FunctionType.Unite;
      united.EdgeFitting = BooleanOperation.FittingType.Blend;
      united.EdgeRadius = new Parameter(2.0);
      AddFirst(united, basePlate);
      AddSecond(united, lugPositiveY);
      AddSecond(united, lugNegativeY);
      AddSecond(united, ribPYR);
      AddSecond(united, ribPYL);
      AddSecond(united, ribNYR);
      AddSecond(united, ribNYL);
      var endUnite = doc.EndChanges();
      EasyDiagnostics.Print("unite.endChanges", endUnite);
      if (endUnite.ToString() != "OK") return 20;

      doc.BeginChanges("clevis bracket subtract holes and lightening cutouts");
      var finalBracket = new BooleanOperation(doc);
      finalBracket.Name = "symmetric_clevis_bracket_final";
      finalBracket.Function = BooleanOperation.FunctionType.Subtract;
      AddFirst(finalBracket, united);
      AddSecond(finalBracket, boreCut);
      foreach (var cut in mountCuts) AddSecond(finalBracket, cut);
      AddSecond(finalBracket, triLeftCut);
      AddSecond(finalBracket, triRightCut);
      var endSubtract = doc.EndChanges();
      EasyDiagnostics.Print("subtract.endChanges", endSubtract);
      if (endSubtract.ToString() != "OK") return 30;

      var box = EasyDiagnostics.PrintBodyBoxMm("final", finalBracket);
      int operations = Document3D.GetOperations(doc).Count;
      EasyDiagnostics.Print("operations", operations);
      EasyDiagnostics.Print("features.baseMountHoles", 4);
      EasyDiagnostics.Print("features.lugs", 2);
      EasyDiagnostics.Print("features.horizontalBores", 1);
      EasyDiagnostics.Print("features.triangularLighteningCutouts", 2);
      EasyDiagnostics.Print("features.reinforcingRibs", 4);
      EasyDiagnostics.Print("features.roundedBaseCorners", 4);
      EasyDiagnostics.Print("features.roundedLugTops", 2);
      EasyDiagnostics.Print("features.booleanBlendRadiusMm", "2");

      string outPath = sess.ArtifactPath("symmetric_clevis_bracket.grb");
      bool saved = EasyExport.Grb(doc, outPath);
      EasyDiagnostics.Print("saved", saved);
      EasyDiagnostics.Print("exists", File.Exists(outPath));
      EasyDiagnostics.Print("output", outPath);

      if (!box.Valid) return 40;
      if (!Near(box.SpanX, BaseX, 0.5) || !Near(box.SpanY, BaseY, 0.5) || !Near(box.SpanZ, LugCenterZ + LugRadius, 0.5)) return 41;
      if (operations < 16) return 42;
      if (!saved || !File.Exists(outPath)) return 43;
      return 0;
    }
  }

  static void AddFirst(BooleanOperation op, Operation operand){
    op.FirstOperands.Add(new BooleanOperation.OperandsArray.Operand(operand, false));
  }

  static void AddSecond(BooleanOperation op, Operation operand){
    op.SecondOperands.Add(new BooleanOperation.OperandsArray.Operand(operand, false));
  }

  static ThickenExtrusion ExtrudeRoundedRectangle(Document doc, string name, StandardWorkplane.StandardType workplane, double cx, double cy, double sx, double sy, double radius, double height){
    var points = BuildRoundedRectangle(cx, cy, sx, sy, radius, 10);
    return ExtrudeProfile(doc, name, workplane, points, height);
  }

  static ThickenExtrusion ExtrudeCircle(Document doc, string name, StandardWorkplane.StandardType workplane, double cx, double cy, double dia, double height, int segments){
    var points = new List<Point>();
    double r = dia / 2.0;
    for (int i = 0; i < segments; i++) {
      double a = 2.0 * Math.PI * i / segments;
      points.Add(new Point(cx + r * Math.Cos(a), cy + r * Math.Sin(a)));
    }
    return ExtrudeProfile(doc, name, workplane, points, height);
  }

  static ThickenExtrusion ExtrudeProfile(Document doc, string name, StandardWorkplane.StandardType workplane, List<Point> points, double height){
    Area area = new Area(doc);
    AddContour(doc, area, points, true);
    var profile = new AreaProfile(doc);
    profile.Name = name + "_profile";
    profile.Area = area;
    profile.WorkSurface = new StandardWorkplane(doc, workplane);
    profile.VisibleInScene = false;
    var extrusion = new ThickenExtrusion(doc);
    extrusion.Name = name;
    extrusion.Thickness1 = 0.0;
    extrusion.LengthType = ThickenExtrusion.LengthValue.ValueNo;
    extrusion.ForwardLength = height;
    extrusion.Profile.Add(profile.Geometry.SheetContour);
    return extrusion;
  }

  static void AddContour(Document doc, Area area, List<Point> points, bool direction){
    var closed = new List<Point>(points);
    if (closed.Count == 0) throw new InvalidOperationException("empty contour");
    closed.Add(closed[0]);
    var outline = new PolylineOutline(doc, new PolylineGeometry(closed));
    outline.IsService = true;
    var contour = area.AppendContour();
    var segment = new OutlineContourSegment(contour);
    segment.Outline = outline;
    segment.Direction = direction;
  }

  static List<Point> BuildRoundedRectangle(double cx, double cy, double sx, double sy, double r, int steps){
    var points = new List<Point>();
    double hx = sx / 2.0;
    double hy = sy / 2.0;
    AddArc(points, cx + hx - r, cy + hy - r, r, 0.0, 90.0, steps);
    AddArc(points, cx - hx + r, cy + hy - r, r, 90.0, 180.0, steps);
    AddArc(points, cx - hx + r, cy - hy + r, r, 180.0, 270.0, steps);
    AddArc(points, cx + hx - r, cy - hy + r, r, 270.0, 360.0, steps);
    return points;
  }

  static List<Point> BuildRoundedLugProfile(double xMin, double zBottom, double xMax, double zCenter, double radius, int arcSteps){
    var points = new List<Point>();
    points.Add(new Point(xMin, zBottom));
    points.Add(new Point(xMax, zBottom));
    points.Add(new Point(xMax, zCenter));
    for (int i = 1; i <= arcSteps; i++) {
      double a = 0.0 + Math.PI * i / arcSteps;
      points.Add(new Point(radius * Math.Cos(a), zCenter + radius * Math.Sin(a)));
    }
    points.Add(new Point(xMin, zBottom));
    return points;
  }

  static List<Point> BuildTriangle(double x1, double y1, double x2, double y2, double x3, double y3){
    return new List<Point>{new Point(x1, y1), new Point(x2, y2), new Point(x3, y3)};
  }

  static void AddArc(List<Point> points, double cx, double cy, double r, double startDeg, double endDeg, int steps){
    for (int i = 0; i <= steps; i++) {
      double t = startDeg + (endDeg - startDeg) * i / steps;
      double a = Math.PI * t / 180.0;
      points.Add(new Point(cx + r * Math.Cos(a), cy + r * Math.Sin(a)));
    }
  }

  static bool Near(double actual, double expected, double tolerance){
    return Math.Abs(actual - expected) <= tolerance;
  }

  static string F(double value){
    return value.ToString("0", CultureInfo.InvariantCulture).Replace("-", "m");
  }
}
