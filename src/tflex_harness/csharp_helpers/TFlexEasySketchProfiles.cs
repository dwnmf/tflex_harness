using System;
using System.Collections.Generic;
using TFlex.Drawing;
using TFlex.Model;
using TFlex.Model.Model2D;
using TFlex.Model.Model3D;

namespace TFlexEasy {
  public static partial class EasyProfiles {
    public static AreaProfile Polygon(Document doc, IList<EasyPoint2> points, string name) {
      if (points == null || points.Count < 3) throw new ArgumentException("Polygon needs at least three points", "points");
      Area area = new Area(doc);
      AddContour(doc, area, ToDrawingPoints(points), true);
      return ProfileOn(doc, area, new StandardWorkplane(doc, StandardWorkplane.StandardType.Top), name);
    }

    public static AreaProfile Rectangle(Document doc, double cxMm, double cyMm, double sxMm, double syMm, string name) {
      double hx = sxMm / 2.0;
      double hy = syMm / 2.0;
      return Polygon(doc, new EasyPoint2[] {
        new EasyPoint2(cxMm - hx, cyMm - hy),
        new EasyPoint2(cxMm + hx, cyMm - hy),
        new EasyPoint2(cxMm + hx, cyMm + hy),
        new EasyPoint2(cxMm - hx, cyMm + hy)
      }, name);
    }

    public static AreaProfile RoundedRectangle(Document doc, double cxMm, double cyMm, double sxMm, double syMm, double radiusMm, string name) {
      Area area = new Area(doc);
      AddContour(doc, area, BuildRoundedRectangle(cxMm, cyMm, sxMm, syMm, radiusMm, 10), true);
      return ProfileOn(doc, area, new StandardWorkplane(doc, StandardWorkplane.StandardType.Top), name);
    }

    public static AreaProfile Triangle(Document doc, EasyPoint2 p1, EasyPoint2 p2, EasyPoint2 p3, string name) {
      return Polygon(doc, new EasyPoint2[] { p1, p2, p3 }, name);
    }

    public static AreaProfile Slot(Document doc, double cxMm, double cyMm, double lengthMm, double widthMm, double angleDeg, string name) {
      Area area = new Area(doc);
      AddContour(doc, area, BuildSlot(cxMm, cyMm, lengthMm, widthMm, angleDeg, 16), true);
      return ProfileOn(doc, area, new StandardWorkplane(doc, StandardWorkplane.StandardType.Top), name);
    }

    public static AreaProfile Obround(Document doc, double cxMm, double cyMm, double lengthMm, double widthMm, double angleDeg, string name) {
      return Slot(doc, cxMm, cyMm, lengthMm, widthMm, angleDeg, name);
    }

    public static AreaProfile LugProfile(Document doc, double radiusMm, double bottomZMm, double centerZMm, string name) {
      Area area = new Area(doc);
      AddContour(doc, area, BuildLug(radiusMm, bottomZMm, centerZMm, 32), true);
      return ProfileOn(doc, area, new StandardWorkplane(doc, StandardWorkplane.StandardType.Front), name);
    }

    public static AreaProfile WithHole(Document doc, IList<EasyPoint2> outer, IList<EasyPoint2> inner, string name) {
      if (outer == null || outer.Count < 3) throw new ArgumentException("Outer contour needs at least three points", "outer");
      if (inner == null || inner.Count < 3) throw new ArgumentException("Inner contour needs at least three points", "inner");
      Area area = new Area(doc);
      AddContour(doc, area, ToDrawingPoints(outer), true);
      AddContour(doc, area, ToDrawingPoints(inner), false);
      return ProfileOn(doc, area, new StandardWorkplane(doc, StandardWorkplane.StandardType.Top), name);
    }

    public static AreaProfile CircleAt(Document doc, double cxMm, double cyMm, double diameterMm, string name) {
      Area area = new Area(doc);
      AddContour(doc, area, BuildCirclePoints(cxMm, cyMm, diameterMm / 2.0, 96), true);
      return ProfileOn(doc, area, new StandardWorkplane(doc, StandardWorkplane.StandardType.Top), name);
    }

    public static AreaProfile ProfileOn(Document doc, Area area, StandardWorkplane workplane, string name) {
      AreaProfile profile = new AreaProfile(doc);
      try { profile.Name = name; }
      catch (Exception ex) { EasyDiagnostics.Print(name + ".profileNameSetError", ex.GetType().Name + ": " + ex.Message); }
      profile.Area = area;
      profile.WorkSurface = workplane;
      profile.VisibleInScene = false;
      return profile;
    }

    static void AddContour(Document doc, Area area, List<Point> points, bool direction) {
      List<Point> closed = new List<Point>(points);
      if (closed.Count == 0) throw new InvalidOperationException("Empty contour");
      Point first = closed[0];
      Point last = closed[closed.Count - 1];
      if (Math.Abs(first.X - last.X) > 1e-9 || Math.Abs(first.Y - last.Y) > 1e-9) closed.Add(first);
      PolylineOutline outline = new PolylineOutline(doc, new PolylineGeometry(closed));
      outline.IsService = true;
      TFlex.Model.Model2D.Contour contour = area.AppendContour();
      OutlineContourSegment segment = new OutlineContourSegment(contour);
      segment.Outline = outline;
      segment.Direction = direction;
    }

    static List<Point> ToDrawingPoints(IList<EasyPoint2> points) {
      List<Point> result = new List<Point>();
      foreach (EasyPoint2 p in points) result.Add(new Point(p.XMm, p.YMm));
      return result;
    }

    static List<Point> BuildCirclePoints(double cx, double cy, double radius, int segments) {
      List<Point> points = new List<Point>();
      for (int i = 0; i < segments; i++) {
        double a = 2.0 * Math.PI * i / segments;
        points.Add(new Point(cx + radius * Math.Cos(a), cy + radius * Math.Sin(a)));
      }
      return points;
    }

    static List<Point> BuildRoundedRectangle(double cx, double cy, double sx, double sy, double radius, int steps) {
      double r = Math.Max(0.0, Math.Min(radius, Math.Min(sx, sy) / 2.0));
      List<Point> points = new List<Point>();
      double hx = sx / 2.0;
      double hy = sy / 2.0;
      AddArc(points, cx + hx - r, cy + hy - r, r, 0.0, 90.0, steps);
      AddArc(points, cx - hx + r, cy + hy - r, r, 90.0, 180.0, steps);
      AddArc(points, cx - hx + r, cy - hy + r, r, 180.0, 270.0, steps);
      AddArc(points, cx + hx - r, cy - hy + r, r, 270.0, 360.0, steps);
      return points;
    }

    static List<Point> BuildSlot(double cx, double cy, double length, double width, double angleDeg, int steps) {
      double straight = Math.Max(0.0, length - width);
      double r = width / 2.0;
      List<Point> raw = new List<Point>();
      AddArc(raw, straight / 2.0, 0.0, r, -90.0, 90.0, steps);
      AddArc(raw, -straight / 2.0, 0.0, r, 90.0, 270.0, steps);
      return RotateTranslate(raw, cx, cy, angleDeg);
    }

    static List<Point> BuildLug(double radius, double bottomZ, double centerZ, int steps) {
      List<Point> points = new List<Point>();
      points.Add(new Point(-radius, bottomZ));
      points.Add(new Point(radius, bottomZ));
      points.Add(new Point(radius, centerZ));
      for (int i = 1; i <= steps; i++) {
        double a = Math.PI * i / steps;
        points.Add(new Point(radius * Math.Cos(a), centerZ + radius * Math.Sin(a)));
      }
      return points;
    }

    static void AddArc(List<Point> points, double cx, double cy, double r, double startDeg, double endDeg, int steps) {
      for (int i = 0; i <= steps; i++) {
        double t = startDeg + (endDeg - startDeg) * i / steps;
        double a = Math.PI * t / 180.0;
        points.Add(new Point(cx + r * Math.Cos(a), cy + r * Math.Sin(a)));
      }
    }

    static List<Point> RotateTranslate(List<Point> raw, double cx, double cy, double angleDeg) {
      double a = Math.PI * angleDeg / 180.0;
      double ca = Math.Cos(a);
      double sa = Math.Sin(a);
      List<Point> result = new List<Point>();
      foreach (Point p in raw) result.Add(new Point(cx + p.X * ca - p.Y * sa, cy + p.X * sa + p.Y * ca));
      return result;
    }
  }
}
