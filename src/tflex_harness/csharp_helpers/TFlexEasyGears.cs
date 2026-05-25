using System;
using System.Collections.Generic;
using TFlex.Drawing;
using TFlex.Model;
using TFlex.Model.Model2D;
using TFlex.Model.Model3D;

namespace TFlexEasy {
  public struct EasyGearToothStyle {
    public double RootHalfWidthFactor;
    public double TipHalfWidthFactor;

    public EasyGearToothStyle(double rootHalfWidthFactor, double tipHalfWidthFactor) {
      RootHalfWidthFactor = rootHalfWidthFactor;
      TipHalfWidthFactor = tipHalfWidthFactor;
    }

    public static EasyGearToothStyle Clearanced {
      get { return new EasyGearToothStyle(0.30, 0.14); }
    }

    public static EasyGearToothStyle Wide {
      get { return new EasyGearToothStyle(0.45, 0.22); }
    }
  }

  public static class EasyGears {
    public static double ToothPitchDeg(int teeth) {
      if (teeth <= 0) throw new ArgumentOutOfRangeException("teeth", "teeth must be positive");
      return 360.0 / teeth;
    }

    public static double PhaseForToothAtAxisDeg(int teeth, double axisDeg) {
      ToothPitchDeg(teeth);
      return axisDeg;
    }

    public static double PhaseForGapAtAxisDeg(int teeth, double axisDeg) {
      return axisDeg - ToothPitchDeg(teeth) / 2.0;
    }

    public static double PlanetToothFacingSunPhaseDeg(double planetAxisDeg) {
      return planetAxisDeg + 180.0;
    }

    public static EasyPoint2[] PlanetCenters(double radiusMm, int count, double startAngleDeg) {
      if (count <= 0) throw new ArgumentOutOfRangeException("count", "count must be positive");
      EasyPoint2[] centers = new EasyPoint2[count];
      for (int i = 0; i < count; i++) {
        centers[i] = EasyPlacement.PolarMm(radiusMm, startAngleDeg + 360.0 * i / count);
      }
      return centers;
    }

    public static AreaProfile CircleAt(Document doc, double centerXMm, double centerYMm, double diameterMm, string name) {
      return CircleAt(doc, centerXMm, centerYMm, diameterMm, 96, name);
    }

    public static AreaProfile CircleAt(Document doc, double centerXMm, double centerYMm, double diameterMm, int segments, string name) {
      EasyDiagnostics.Print(name + ".centerMm", EasyUnits.F(centerXMm) + "," + EasyUnits.F(centerYMm));
      EasyDiagnostics.Print(name + ".diameterMm", EasyUnits.F(diameterMm));
      Area area = new Area(doc);
      AddClosedPolylineContour(doc, area, BuildCircle(centerXMm, centerYMm, diameterMm / 2.0, segments), true);
      return MakeAreaProfile(doc, area, name);
    }

    public static AreaProfile ExternalTrapezoidGearAt(Document doc, double centerXMm, double centerYMm, int teeth, double rootDiaMm, double outerDiaMm, double phaseDeg, string name) {
      return ExternalTrapezoidGearAt(doc, centerXMm, centerYMm, teeth, rootDiaMm, outerDiaMm, phaseDeg, EasyGearToothStyle.Clearanced, name);
    }

    public static AreaProfile ExternalTrapezoidGearAt(Document doc, double centerXMm, double centerYMm, int teeth, double rootDiaMm, double outerDiaMm, double phaseDeg, EasyGearToothStyle style, string name) {
      PrintExternalGearInputs(name, centerXMm, centerYMm, teeth, rootDiaMm, outerDiaMm, phaseDeg, style);
      Area area = new Area(doc);
      AddClosedPolylineContour(doc, area, BuildExternalGear(centerXMm, centerYMm, rootDiaMm / 2.0, outerDiaMm / 2.0, teeth, DegToRad(phaseDeg), style), true);
      return MakeAreaProfile(doc, area, name);
    }

    public static AreaProfile ExternalTrapezoidGearWithBoreAt(Document doc, double centerXMm, double centerYMm, int teeth, double rootDiaMm, double outerDiaMm, double boreDiaMm, double phaseDeg, string name) {
      return ExternalTrapezoidGearWithBoreAt(doc, centerXMm, centerYMm, teeth, rootDiaMm, outerDiaMm, boreDiaMm, phaseDeg, EasyGearToothStyle.Clearanced, name);
    }

    public static AreaProfile ExternalTrapezoidGearWithBoreAt(Document doc, double centerXMm, double centerYMm, int teeth, double rootDiaMm, double outerDiaMm, double boreDiaMm, double phaseDeg, EasyGearToothStyle style, string name) {
      PrintExternalGearInputs(name, centerXMm, centerYMm, teeth, rootDiaMm, outerDiaMm, phaseDeg, style);
      EasyDiagnostics.Print(name + ".boreDiaMm", EasyUnits.F(boreDiaMm));
      Area area = new Area(doc);
      AddClosedPolylineContour(doc, area, BuildExternalGear(centerXMm, centerYMm, rootDiaMm / 2.0, outerDiaMm / 2.0, teeth, DegToRad(phaseDeg), style), true);
      AddClosedPolylineContour(doc, area, BuildCircle(centerXMm, centerYMm, boreDiaMm / 2.0, 72), false);
      return MakeAreaProfile(doc, area, name);
    }

    public static AreaProfile InternalTrapezoidGearRingAt(Document doc, double centerXMm, double centerYMm, int teeth, double outerDiaMm, double internalRootDiaMm, double toothTipDiaMm, double phaseDeg, string name) {
      return InternalTrapezoidGearRingAt(doc, centerXMm, centerYMm, teeth, outerDiaMm, internalRootDiaMm, toothTipDiaMm, phaseDeg, EasyGearToothStyle.Clearanced, name);
    }

    public static AreaProfile InternalTrapezoidGearRingAt(Document doc, double centerXMm, double centerYMm, int teeth, double outerDiaMm, double internalRootDiaMm, double toothTipDiaMm, double phaseDeg, EasyGearToothStyle style, string name) {
      EasyDiagnostics.Print(name + ".centerMm", EasyUnits.F(centerXMm) + "," + EasyUnits.F(centerYMm));
      EasyDiagnostics.Print(name + ".teeth", teeth);
      EasyDiagnostics.Print(name + ".outerDiaMm", EasyUnits.F(outerDiaMm));
      EasyDiagnostics.Print(name + ".internalRootDiaMm", EasyUnits.F(internalRootDiaMm));
      EasyDiagnostics.Print(name + ".toothTipDiaMm", EasyUnits.F(toothTipDiaMm));
      EasyDiagnostics.Print(name + ".phaseDeg", EasyUnits.F(phaseDeg));
      EasyDiagnostics.Print(name + ".rootHalfWidthFactor", EasyUnits.F(style.RootHalfWidthFactor));
      EasyDiagnostics.Print(name + ".tipHalfWidthFactor", EasyUnits.F(style.TipHalfWidthFactor));
      Area area = new Area(doc);
      AddClosedPolylineContour(doc, area, BuildCircle(centerXMm, centerYMm, outerDiaMm / 2.0, 240), true);
      AddClosedPolylineContour(doc, area, BuildInternalGearBoundary(centerXMm, centerYMm, internalRootDiaMm / 2.0, toothTipDiaMm / 2.0, teeth, DegToRad(phaseDeg), style), false);
      return MakeAreaProfile(doc, area, name);
    }

    public static double ExternalExternalRadialClearanceMm(double centerDistanceMm, double outerDiaAmm, double outerDiaBmm) {
      return centerDistanceMm - outerDiaAmm / 2.0 - outerDiaBmm / 2.0;
    }

    public static double InternalExternalRadialClearanceMm(double internalRootDiaMm, double centerDistanceMm, double externalOuterDiaMm) {
      return internalRootDiaMm / 2.0 - centerDistanceMm - externalOuterDiaMm / 2.0;
    }

    public static void PrintPlanetCenterEvidence(string name, Operation body) {
      BodyBoxMm box = EasyDiagnostics.GetBodyBoxMm(body);
      double cx = (box.MinX + box.MaxX) / 2.0;
      double cy = (box.MinY + box.MaxY) / 2.0;
      double radius = Math.Sqrt(cx * cx + cy * cy);
      EasyDiagnostics.Print(name + ".bboxCenterMm", EasyUnits.F(cx) + "," + EasyUnits.F(cy));
      EasyDiagnostics.Print(name + ".bboxCenterRadiusMm", EasyUnits.F(radius));
    }

    static void PrintExternalGearInputs(string name, double centerXMm, double centerYMm, int teeth, double rootDiaMm, double outerDiaMm, double phaseDeg, EasyGearToothStyle style) {
      EasyDiagnostics.Print(name + ".centerMm", EasyUnits.F(centerXMm) + "," + EasyUnits.F(centerYMm));
      EasyDiagnostics.Print(name + ".teeth", teeth);
      EasyDiagnostics.Print(name + ".rootDiaMm", EasyUnits.F(rootDiaMm));
      EasyDiagnostics.Print(name + ".outerDiaMm", EasyUnits.F(outerDiaMm));
      EasyDiagnostics.Print(name + ".phaseDeg", EasyUnits.F(phaseDeg));
      EasyDiagnostics.Print(name + ".rootHalfWidthFactor", EasyUnits.F(style.RootHalfWidthFactor));
      EasyDiagnostics.Print(name + ".tipHalfWidthFactor", EasyUnits.F(style.TipHalfWidthFactor));
    }

    static AreaProfile MakeAreaProfile(Document doc, Area area, string name) {
      StandardWorkplane top = new StandardWorkplane(doc, StandardWorkplane.StandardType.Top);
      AreaProfile profile = new AreaProfile(doc);
      profile.Name = name;
      profile.Area = area;
      profile.WorkSurface = top;
      profile.VisibleInScene = false;
      return profile;
    }

    static void AddClosedPolylineContour(Document doc, Area area, List<Point> points, bool direction) {
      List<Point> closed = new List<Point>(points);
      if (closed.Count == 0) throw new InvalidOperationException("Empty contour");
      Point first = closed[0];
      Point last = closed[closed.Count - 1];
      if (Math.Abs(first.X - last.X) > 1e-9 || Math.Abs(first.Y - last.Y) > 1e-9) {
        closed.Add(new Point(first.X, first.Y));
      }
      PolylineOutline outline = new PolylineOutline(doc, new PolylineGeometry(closed));
      outline.IsService = true;
      TFlex.Model.Model2D.Contour contour = area.AppendContour();
      OutlineContourSegment segment = new OutlineContourSegment(contour);
      segment.Outline = outline;
      segment.Direction = direction;
    }

    static List<Point> BuildExternalGear(double cx, double cy, double rootRadius, double tipRadius, int teeth, double phaseRad, EasyGearToothStyle style) {
      List<Point> points = new List<Point>();
      double step = 2.0 * Math.PI / teeth;
      for (int i = 0; i < teeth; i++) {
        double center = phaseRad + i * step;
        AddPolar(points, cx, cy, rootRadius, center - step * style.RootHalfWidthFactor);
        AddPolar(points, cx, cy, tipRadius, center - step * style.TipHalfWidthFactor);
        AddPolar(points, cx, cy, tipRadius, center + step * style.TipHalfWidthFactor);
        AddPolar(points, cx, cy, rootRadius, center + step * style.RootHalfWidthFactor);
      }
      return points;
    }

    static List<Point> BuildInternalGearBoundary(double cx, double cy, double rootRadius, double inwardTipRadius, int teeth, double phaseRad, EasyGearToothStyle style) {
      List<Point> points = new List<Point>();
      double step = 2.0 * Math.PI / teeth;
      for (int i = 0; i < teeth; i++) {
        double center = phaseRad + i * step;
        AddPolar(points, cx, cy, rootRadius, center - step * style.RootHalfWidthFactor);
        AddPolar(points, cx, cy, inwardTipRadius, center - step * style.TipHalfWidthFactor);
        AddPolar(points, cx, cy, inwardTipRadius, center + step * style.TipHalfWidthFactor);
        AddPolar(points, cx, cy, rootRadius, center + step * style.RootHalfWidthFactor);
      }
      return points;
    }

    static List<Point> BuildCircle(double cx, double cy, double radius, int segments) {
      List<Point> points = new List<Point>();
      for (int i = 0; i < segments; i++) {
        double angle = 2.0 * Math.PI * i / segments;
        AddPolar(points, cx, cy, radius, angle);
      }
      return points;
    }

    static void AddPolar(List<Point> points, double cx, double cy, double radius, double angle) {
      points.Add(new Point(cx + radius * Math.Cos(angle), cy + radius * Math.Sin(angle)));
    }

    static double DegToRad(double deg) {
      return deg * Math.PI / 180.0;
    }
  }
}
