using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using TFlex;
using TFlex.Drawing;
using TFlex.Model;
using TFlex.Model.Model2D;
using TFlex.Model.Model3D;

public class Program {
  const double PlanetCircleRadius = 42.0;
  const double GearThickness = 6.0;
  const double CarrierThickness = 3.0;
  const double PinDiameter = 6.0;
  const double PinHeight = 11.0;

  public static int Main(){
    string output = Environment.GetEnvironmentVariable("TFLEX_RECIPE_OUTPUT_FILE");
    if (String.IsNullOrWhiteSpace(output)) output = Path.GetFullPath("planetary_gear_assembly.grb");
    string dir = Path.GetDirectoryName(output);
    if (!String.IsNullOrWhiteSpace(dir)) Directory.CreateDirectory(dir);

    var setup = new ApplicationSessionSetup();
    setup.ReadOnly = false;
    setup.Enable3D = true;
    setup.EnableDOCs = false;
    setup.EnableMacros = false;
    setup.PromptToSaveModifiedDocuments = false;
    setup.ProtectionLicense = ApplicationSessionSetup.License.TFlex3D;

    bool init = Application.InitSession(setup);
    Console.WriteLine("init=" + init);
    if (!init) return 10;

    Document doc = null;
    try {
      doc = Application.NewDocument(true, false);
      Console.WriteLine("docNull=" + (doc == null));
      if (doc == null) return 11;

      doc.BeginChanges("create flat planetary gear assembly");
      StandardWorkplane top = new StandardWorkplane(doc, StandardWorkplane.StandardType.Top);

      ThickenExtrusion sun = MakeProfileBody(
        doc,
        top,
        "sun_gear_18_simplified_trapezoid_teeth",
        BuildExternalGear(0.0, 0.0, 18.0, 22.0, 18, 0.0),
        GearThickness,
        44
      );
      sun.Fixed = true;

      ThickenExtrusion ring = MakeRingBody(
        doc,
        top,
        "ring_gear_internal_54_simplified_trapezoid_teeth",
        78.0,
        BuildInternalGearBoundary(0.0, 0.0, 68.0, 62.0, 54, 0.0),
        GearThickness,
        84
      );
      ring.Fixed = true;
      ring.Transparency = 0.18;

      ThickenExtrusion carrier = MakeProfileBody(
        doc,
        top,
        "three_arm_carrier_body",
        BuildCarrier(0.0, 0.0),
        CarrierThickness,
        30
      );
      AddMove(carrier, "place carrier under gear plane", 0.0, 0.0, -CarrierThickness);

      List<ThickenExtrusion> planets = new List<ThickenExtrusion>();
      List<Cylinder> pins = new List<Cylinder>();
      for (int i = 0; i < 3; i++) {
        double angleDeg = i * 120.0;
        double angleRad = Deg(angleDeg);
        double cx = PlanetCircleRadius * Math.Cos(angleRad);
        double cy = PlanetCircleRadius * Math.Sin(angleRad);

        ThickenExtrusion planet = MakeProfileBody(
          doc,
          top,
          "planet_gear_" + (i + 1).ToString("00") + "_12_simplified_trapezoid_teeth",
          BuildExternalGear(cx, cy, 14.0, 18.0, 12, angleRad + Deg(15.0)),
          GearThickness,
          12 + i
        );
        planets.Add(planet);

        Cylinder pin = MakeCylinder(
          doc,
          "planet_pin_" + (i + 1).ToString("00"),
          PinDiameter,
          PinHeight,
          cx,
          cy,
          PinHeight / 2.0,
          70 + i
        );
        pins.Add(pin);

        Console.WriteLine("planetCenter" + (i + 1).ToString(CultureInfo.InvariantCulture) + "=" + Format(cx) + "," + Format(cy));
        Console.WriteLine("planetRadiusDistance" + (i + 1).ToString(CultureInfo.InvariantCulture) + "=" + Format(Math.Sqrt(cx * cx + cy * cy)));
      }

      var end = doc.EndChanges();
      Console.WriteLine("endChanges=" + end);
      if (end.ToString() != "OK") return 12;

      int operations = Document3D.GetOperations(doc).Count;
      int mates = Document3D.GetMates(doc).Count;
      Console.WriteLine("operations=" + operations);
      Console.WriteLine("mates=" + mates);
      Console.WriteLine("sunBodies=1");
      Console.WriteLine("planetBodies=" + planets.Count);
      Console.WriteLine("ringBodies=1");
      Console.WriteLine("carrierBodies=1");
      Console.WriteLine("pinBodies=" + pins.Count);
      Console.WriteLine("sunTeeth=18");
      Console.WriteLine("planetTeethEach=12");
      Console.WriteLine("ringInternalTeeth=54");
      Console.WriteLine("planetCircleRadiusMm=" + Format(PlanetCircleRadius));

      bool bodyNull = false;
      bool bboxPositive = true;
      double minX = Double.PositiveInfinity;
      double minY = Double.PositiveInfinity;
      double minZ = Double.PositiveInfinity;
      double maxX = Double.NegativeInfinity;
      double maxY = Double.NegativeInfinity;
      double maxZ = Double.NegativeInfinity;
      foreach (Operation op in Document3D.GetOperations(doc)) {
        bodyNull = bodyNull || op.Body == null || op.Geometry == null;
        if (op.Geometry == null) {
          bboxPositive = false;
          continue;
        }
        var box = op.Geometry.AABoundBox;
        double sx = Math.Abs(box.Maximum.X - box.Minimum.X);
        double sy = Math.Abs(box.Maximum.Y - box.Minimum.Y);
        double sz = Math.Abs(box.Maximum.Z - box.Minimum.Z);
        bool positive = box.Valid && sx > 0 && sy > 0 && sz > 0;
        bboxPositive = bboxPositive && positive;
        if (box.Valid) {
          minX = Math.Min(minX, box.Minimum.X);
          minY = Math.Min(minY, box.Minimum.Y);
          minZ = Math.Min(minZ, box.Minimum.Z);
          maxX = Math.Max(maxX, box.Maximum.X);
          maxY = Math.Max(maxY, box.Maximum.Y);
          maxZ = Math.Max(maxZ, box.Maximum.Z);
        }
      }

      double spanX = maxX - minX;
      double spanY = maxY - minY;
      double spanZ = maxZ - minZ;
      Console.WriteLine("bodyNull=" + bodyNull);
      Console.WriteLine("bboxPositive=" + bboxPositive);
      Console.WriteLine("bboxMin=" + Format(minX) + "," + Format(minY) + "," + Format(minZ));
      Console.WriteLine("bboxMax=" + Format(maxX) + "," + Format(maxY) + "," + Format(maxZ));
      Console.WriteLine("bboxSpan=" + Format(spanX) + "," + Format(spanY) + "," + Format(spanZ));

      bool saved = doc.SaveAs(output);
      Console.WriteLine("saved=" + saved);
      Console.WriteLine("exists=" + File.Exists(output));
      Console.WriteLine("output=" + output);

      if (operations != 9) return 13;
      if (bodyNull || !bboxPositive) return 14;
      if (spanX < 0.15 || spanY < 0.15 || spanZ < 0.009) return 15;
      if (!saved || !File.Exists(output)) return 16;
      return 0;
    } catch (Exception ex) {
      Console.WriteLine("exceptionType=" + ex.GetType().FullName);
      Console.WriteLine("exception=" + ex.Message);
      Console.WriteLine(ex.ToString());
      return 99;
    } finally {
      try { if (doc != null) doc.Close(); } catch (Exception closeEx) { Console.WriteLine("closeException=" + closeEx.Message); }
      if (Application.IsSessionInitialized) Application.ExitSession();
      Console.WriteLine("session=" + Application.IsSessionInitialized);
    }
  }

  static ThickenExtrusion MakeProfileBody(Document doc, StandardWorkplane top, string name, List<Point> boundary, double height, int color){
    Area area = new Area(doc);
    AddClosedPolylineContour(doc, area, boundary, true);

    AreaProfile profile = new AreaProfile(doc);
    profile.Area = area;
    profile.WorkSurface = top;

    ThickenExtrusion body = new ThickenExtrusion(doc);
    body.Name = name;
    body.Color = color;
    body.MeshDensity = 0.7;
    body.Thickness1 = 1.0;
    body.LengthType = ThickenExtrusion.LengthValue.AutoValue;
    body.ForwardLength = height;
    body.Profile.Add(profile.Geometry.SheetContour);
    return body;
  }

  static ThickenExtrusion MakeRingBody(Document doc, StandardWorkplane top, string name, double outerRadius, List<Point> innerBoundary, double height, int color){
    Area area = new Area(doc);
    AddClosedPolylineContour(doc, area, BuildCircle(0.0, 0.0, outerRadius, 144), true);
    AddClosedPolylineContour(doc, area, innerBoundary, false);

    AreaProfile profile = new AreaProfile(doc);
    profile.Area = area;
    profile.WorkSurface = top;

    ThickenExtrusion body = new ThickenExtrusion(doc);
    body.Name = name;
    body.Color = color;
    body.MeshDensity = 0.7;
    body.Thickness1 = 1.0;
    body.LengthType = ThickenExtrusion.LengthValue.AutoValue;
    body.ForwardLength = height;
    body.Profile.Add(profile.Geometry.SheetContour);
    return body;
  }

  static Cylinder MakeCylinder(Document doc, string name, double diameter, double height, double x, double y, double z, int color){
    Cylinder cylinder = new Cylinder(doc);
    cylinder.Name = name;
    cylinder.Color = color;
    cylinder.Symmetry = true;
    cylinder.Diameter = new Parameter(diameter);
    cylinder.Height = new Parameter(height);
    AddMove(cylinder, "position " + name, x, y, z);
    return cylinder;
  }

  static void AddClosedPolylineContour(Document doc, Area area, List<Point> points, bool direction){
    List<Point> closed = new List<Point>(points);
    if (closed.Count == 0) throw new InvalidOperationException("Empty contour");
    Point first = closed[0];
    Point last = closed[closed.Count - 1];
    if (Math.Abs(first.X - last.X) > 1e-9 || Math.Abs(first.Y - last.Y) > 1e-9) {
      closed.Add(new Point(first.X, first.Y));
    }
    PolylineOutline outline = new PolylineOutline(doc, new PolylineGeometry(closed));
    TFlex.Model.Model2D.Contour contour = area.AppendContour();
    OutlineContourSegment segment = new OutlineContourSegment(contour);
    segment.Outline = outline;
    segment.Direction = direction;
  }

  static List<Point> BuildExternalGear(double cx, double cy, double rootRadius, double tipRadius, int teeth, double phaseRad){
    List<Point> points = new List<Point>();
    double step = 2.0 * Math.PI / teeth;
    for (int i = 0; i < teeth; i++) {
      double center = phaseRad + i * step;
      AddPolar(points, cx, cy, rootRadius, center - step * 0.45);
      AddPolar(points, cx, cy, tipRadius, center - step * 0.22);
      AddPolar(points, cx, cy, tipRadius, center + step * 0.22);
      AddPolar(points, cx, cy, rootRadius, center + step * 0.45);
    }
    return points;
  }

  static List<Point> BuildInternalGearBoundary(double cx, double cy, double rootRadius, double inwardTipRadius, int teeth, double phaseRad){
    List<Point> points = new List<Point>();
    double step = 2.0 * Math.PI / teeth;
    for (int i = 0; i < teeth; i++) {
      double center = phaseRad + i * step;
      AddPolar(points, cx, cy, rootRadius, center - step * 0.45);
      AddPolar(points, cx, cy, inwardTipRadius, center - step * 0.22);
      AddPolar(points, cx, cy, inwardTipRadius, center + step * 0.22);
      AddPolar(points, cx, cy, rootRadius, center + step * 0.45);
    }
    return points;
  }

  static List<Point> BuildCarrier(double cx, double cy){
    List<Point> points = new List<Point>();
    for (int i = 0; i < 3; i++) {
      double center = Deg(i * 120.0);
      AddPolar(points, cx, cy, 17.0, center - Deg(54.0));
      AddPolar(points, cx, cy, 29.0, center - Deg(28.0));
      AddPolar(points, cx, cy, 48.0, center - Deg(11.0));
      AddPolar(points, cx, cy, 48.0, center + Deg(11.0));
      AddPolar(points, cx, cy, 29.0, center + Deg(28.0));
      AddPolar(points, cx, cy, 17.0, center + Deg(54.0));
    }
    return points;
  }

  static List<Point> BuildCircle(double cx, double cy, double radius, int segments){
    List<Point> points = new List<Point>();
    for (int i = 0; i < segments; i++) {
      double angle = 2.0 * Math.PI * i / segments;
      AddPolar(points, cx, cy, radius, angle);
    }
    return points;
  }

  static void AddPolar(List<Point> points, double cx, double cy, double radius, double angle){
    points.Add(new Point(cx + radius * Math.Cos(angle), cy + radius * Math.Sin(angle)));
  }

  static void AddMove(Object3D obj, string name, double x, double y, double z){
    TransformationGroup group = obj.Transformations.AddBaseTransfGroup();
    group.Name = name;
    group.AddMoveTransf(TransformationCoordinate.X, new Parameter(MmToModel(x)));
    group.AddMoveTransf(TransformationCoordinate.Y, new Parameter(MmToModel(y)));
    group.AddMoveTransf(TransformationCoordinate.Z, new Parameter(MmToModel(z)));
  }

  static double Deg(double value){
    return value * Math.PI / 180.0;
  }

  static double MmToModel(double value){
    return value / 1000.0;
  }

  static string Format(double value){
    return value.ToString("0.########", CultureInfo.InvariantCulture);
  }
}
