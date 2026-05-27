using System.Collections.Generic;
using TFlex.Drawing;
using TFlex.Model;
using TFlex.Model.Model2D;
using TFlex.Model.Model3D;

namespace TFlexEasy {
  public static partial class EasyProfiles {
    public static AreaProfile Circle(Document doc, double diameterMm, string name) {
      Area area = new Area(doc);
      AddClosedPolylineContour(doc, area, BuildCircle(0.0, 0.0, diameterMm / 2.0, 96), true);
      return MakeAreaProfile(doc, area, name);
    }

    public static AreaProfile Circle(Document doc, double diameterMm) {
      return Circle(doc, diameterMm, "circle_profile");
    }

    public static AreaProfile Ring(Document doc, double outerDiaMm, double innerDiaMm, string name) {
      Area area = new Area(doc);
      AddClosedPolylineContour(doc, area, BuildCircle(0.0, 0.0, outerDiaMm / 2.0, 144), true);
      AddClosedPolylineContour(doc, area, BuildCircle(0.0, 0.0, innerDiaMm / 2.0, 96), false);
      return MakeAreaProfile(doc, area, name);
    }

    public static AreaProfile Ring(Document doc, double outerDiaMm, double innerDiaMm) {
      return Ring(doc, outerDiaMm, innerDiaMm, "ring_profile");
    }

    public static AreaProfile ExternalTrapezoidGear(Document doc, int teeth, double rootDiaMm, double outerDiaMm, string name) {
      EasyDiagnostics.Print(name + ".teeth", teeth);
      EasyDiagnostics.Print(name + ".rootDiaMm", EasyUnits.F(rootDiaMm));
      EasyDiagnostics.Print(name + ".outerDiaMm", EasyUnits.F(outerDiaMm));
      Area area = new Area(doc);
      AddClosedPolylineContour(doc, area, BuildExternalGear(0.0, 0.0, rootDiaMm / 2.0, outerDiaMm / 2.0, teeth, 0.0), true);
      return MakeAreaProfile(doc, area, name);
    }

    public static AreaProfile ExternalTrapezoidGear(Document doc, int teeth, double rootDiaMm, double outerDiaMm) {
      return ExternalTrapezoidGear(doc, teeth, rootDiaMm, outerDiaMm, "external_gear_profile");
    }

    public static AreaProfile ExternalTrapezoidGearWithBore(Document doc, int teeth, double rootDiaMm, double outerDiaMm, double boreDiaMm, string name) {
      EasyDiagnostics.Print(name + ".teeth", teeth);
      EasyDiagnostics.Print(name + ".rootDiaMm", EasyUnits.F(rootDiaMm));
      EasyDiagnostics.Print(name + ".outerDiaMm", EasyUnits.F(outerDiaMm));
      EasyDiagnostics.Print(name + ".boreDiaMm", EasyUnits.F(boreDiaMm));
      Area area = new Area(doc);
      AddClosedPolylineContour(doc, area, BuildExternalGear(0.0, 0.0, rootDiaMm / 2.0, outerDiaMm / 2.0, teeth, 0.0), true);
      AddClosedPolylineContour(doc, area, BuildCircle(0.0, 0.0, boreDiaMm / 2.0, 72), false);
      return MakeAreaProfile(doc, area, name);
    }

    public static AreaProfile ExternalTrapezoidGearWithBore(Document doc, int teeth, double rootDiaMm, double outerDiaMm, double boreDiaMm) {
      return ExternalTrapezoidGearWithBore(doc, teeth, rootDiaMm, outerDiaMm, boreDiaMm, "external_gear_bore_profile");
    }

    public static AreaProfile InternalTrapezoidGearRing(Document doc, int teeth, double outerDiaMm, double internalRootDiaMm, double toothTipDiaMm, string name) {
      EasyDiagnostics.Print(name + ".teeth", teeth);
      EasyDiagnostics.Print(name + ".outerDiaMm", EasyUnits.F(outerDiaMm));
      EasyDiagnostics.Print(name + ".internalRootDiaMm", EasyUnits.F(internalRootDiaMm));
      EasyDiagnostics.Print(name + ".toothTipDiaMm", EasyUnits.F(toothTipDiaMm));
      Area area = new Area(doc);
      AddClosedPolylineContour(doc, area, BuildCircle(0.0, 0.0, outerDiaMm / 2.0, 180), true);
      AddClosedPolylineContour(doc, area, BuildInternalGearBoundary(0.0, 0.0, internalRootDiaMm / 2.0, toothTipDiaMm / 2.0, teeth, 0.0), false);
      return MakeAreaProfile(doc, area, name);
    }

    public static AreaProfile InternalTrapezoidGearRing(Document doc, int teeth, double outerDiaMm, double internalRootDiaMm, double toothTipDiaMm) {
      return InternalTrapezoidGearRing(doc, teeth, outerDiaMm, internalRootDiaMm, toothTipDiaMm, "internal_gear_ring_profile");
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
      if (closed.Count == 0) throw new System.InvalidOperationException("Empty contour");
      Point first = closed[0];
      Point last = closed[closed.Count - 1];
      if (System.Math.Abs(first.X - last.X) > 1e-9 || System.Math.Abs(first.Y - last.Y) > 1e-9) {
        closed.Add(new Point(first.X, first.Y));
      }
      PolylineOutline outline = new PolylineOutline(doc, new PolylineGeometry(closed));
      outline.IsService = true;
      TFlex.Model.Model2D.Contour contour = area.AppendContour();
      OutlineContourSegment segment = new OutlineContourSegment(contour);
      segment.Outline = outline;
      segment.Direction = direction;
    }

    static List<Point> BuildExternalGear(double cx, double cy, double rootRadius, double tipRadius, int teeth, double phaseRad) {
      List<Point> points = new List<Point>();
      double step = 2.0 * System.Math.PI / teeth;
      for (int i = 0; i < teeth; i++) {
        double center = phaseRad + i * step;
        AddPolar(points, cx, cy, rootRadius, center - step * 0.45);
        AddPolar(points, cx, cy, tipRadius, center - step * 0.22);
        AddPolar(points, cx, cy, tipRadius, center + step * 0.22);
        AddPolar(points, cx, cy, rootRadius, center + step * 0.45);
      }
      return points;
    }

    static List<Point> BuildInternalGearBoundary(double cx, double cy, double rootRadius, double inwardTipRadius, int teeth, double phaseRad) {
      List<Point> points = new List<Point>();
      double step = 2.0 * System.Math.PI / teeth;
      for (int i = 0; i < teeth; i++) {
        double center = phaseRad + i * step;
        AddPolar(points, cx, cy, rootRadius, center - step * 0.45);
        AddPolar(points, cx, cy, inwardTipRadius, center - step * 0.22);
        AddPolar(points, cx, cy, inwardTipRadius, center + step * 0.22);
        AddPolar(points, cx, cy, rootRadius, center + step * 0.45);
      }
      return points;
    }

    static List<Point> BuildCircle(double cx, double cy, double radius, int segments) {
      List<Point> points = new List<Point>();
      for (int i = 0; i < segments; i++) {
        double angle = 2.0 * System.Math.PI * i / segments;
        AddPolar(points, cx, cy, radius, angle);
      }
      return points;
    }

    static void AddPolar(List<Point> points, double cx, double cy, double radius, double angle) {
      points.Add(new Point(cx + radius * System.Math.Cos(angle), cy + radius * System.Math.Sin(angle)));
    }
  }
}
