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
  const int SunTeeth = 18;
  const int PlanetTeeth = 12;
  const int RingTeeth = 54;

  public static int Main(){
    string output = Environment.GetEnvironmentVariable("TFLEX_RECIPE_OUTPUT_FILE");
    if (String.IsNullOrWhiteSpace(output)) output = Path.GetFullPath("planetary_gear_motion_parametric.grb");
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

      Variable carrierAngle = null;
      Variable planetRadius = null;
      Variable sunAngle = null;
      Variable planetSpinAngle = null;
      Variable[] planetTheta = new Variable[3];
      Variable[] planetX = new Variable[3];
      Variable[] planetY = new Variable[3];
      Variable[] planetSpin = new Variable[3];

      doc.BeginChanges("create planetary drive variables");
      carrierAngle = new Variable(doc, "CarrierAngle", 20.0, true);
      planetRadius = new Variable(doc, "Planet_R_mm", PlanetCircleRadius, true);
      new Variable(doc, "Sun_teeth", SunTeeth, true);
      new Variable(doc, "Planet_teeth", PlanetTeeth, true);
      new Variable(doc, "Ring_teeth", RingTeeth, true);
      sunAngle = new Variable(doc, "SunAngle", "4 * CarrierAngle");
      planetSpinAngle = new Variable(doc, "PlanetSpinAngle", "-7 * CarrierAngle / 2");
      for (int i = 0; i < 3; i++) {
        int index = i + 1;
        double baseAngle = i * 120.0;
        planetTheta[i] = new Variable(doc, "P" + index.ToString(CultureInfo.InvariantCulture) + "_Theta", "CarrierAngle + " + Format(baseAngle));
        planetX[i] = new Variable(doc, "P" + index.ToString(CultureInfo.InvariantCulture) + "_X_m", "Planet_R_mm*cos(P" + index.ToString(CultureInfo.InvariantCulture) + "_Theta) / 1000");
        planetY[i] = new Variable(doc, "P" + index.ToString(CultureInfo.InvariantCulture) + "_Y_m", "Planet_R_mm*sin(P" + index.ToString(CultureInfo.InvariantCulture) + "_Theta) / 1000");
        planetSpin[i] = new Variable(doc, "P" + index.ToString(CultureInfo.InvariantCulture) + "_SpinAngle", "PlanetSpinAngle + " + Format(15.0 + baseAngle));
      }
      var varsEnd = doc.EndChanges();
      Console.WriteLine("variablesEndChanges=" + varsEnd);
      if (varsEnd.ToString() != "OK") return 12;

      doc.BeginChanges("create parametric planetary gear motion assembly");
      StandardWorkplane top = new StandardWorkplane(doc, StandardWorkplane.StandardType.Top);
      Layer hiddenSketchLayer = new Layer(doc);
      hiddenSketchLayer.Name = "hidden_2d_profile_outlines";
      hiddenSketchLayer.Hidden = true;
      hiddenSketchLayer.Frozen = true;

      ThickenExtrusion sun = MakeProfileBody(
        doc,
        top,
        "sun_gear_18_teeth_driven_by_SunAngle",
        BuildExternalGear(0.0, 0.0, 18.0, 22.0, SunTeeth, 0.0),
        GearThickness,
        44,
        null,
        hiddenSketchLayer
      );
      AddRotateZ(sun, "sun gear rotation = 4 * CarrierAngle", sunAngle);

      ThickenExtrusion ring = MakeRingBody(
        doc,
        top,
        "ring_gear_fixed_54_internal_teeth",
        78.0,
        BuildInternalGearBoundary(0.0, 0.0, 68.0, 62.0, RingTeeth, 0.0),
        GearThickness,
        84,
        hiddenSketchLayer
      );
      ring.Fixed = true;
      ring.Transparency = 0.18;

      ThickenExtrusion carrier = MakeProfileBody(
        doc,
        top,
        "carrier_visible_frame_45deg",
        BuildCarrier(0.0, 0.0, Deg(45.0)),
        CarrierThickness,
        30,
        null,
        hiddenSketchLayer
      );

      List<ThickenExtrusion> planets = new List<ThickenExtrusion>();
      List<Cylinder> pins = new List<Cylinder>();
      for (int i = 0; i < 3; i++) {
        int index = i + 1;
        ThickenExtrusion planet = MakeProfileBody(
          doc,
          top,
          "planet_" + index.ToString("00") + "_center_parametric_spin_parametric",
          BuildExternalGear(0.0, 0.0, 14.0, 18.0, PlanetTeeth, Deg(15.0)),
          GearThickness,
          12 + i,
          BuildCircle(0.0, 0.0, PinDiameter / 2.0 + 0.35, 36),
          hiddenSketchLayer
        );
        AddMove(planet, "planet " + index.ToString(CultureInfo.InvariantCulture) + " concentric with pin variables", new Parameter(planetX[i]), new Parameter(planetY[i]), new Parameter(0.0));
        planets.Add(planet);

        Cylinder pin = MakeCylinder(
          doc,
          "pin_" + index.ToString("00") + "_same_center_variables_as_planet",
          PinDiameter,
          PinHeight,
          70 + i
        );
        AddMove(pin, "pin " + index.ToString(CultureInfo.InvariantCulture) + " concentric with planet variables", new Parameter(planetX[i]), new Parameter(planetY[i]), new Parameter(MmToModel(PinHeight / 2.0)));
        pins.Add(pin);
      }

      var geomEnd = doc.EndChanges();
      Console.WriteLine("geometryEndChanges=" + geomEnd);
      if (geomEnd.ToString() != "OK") return 20;

      PrintDriveState("initial", carrierAngle, sunAngle, planetSpinAngle, planetX, planetY, planetSpin);

      doc.BeginChanges("drive CarrierAngle to second motion position");
      carrierAngle.RealValue = 45.0;
      var driveEnd = doc.EndChanges();
      Console.WriteLine("driveEndChanges=" + driveEnd);
      if (driveEnd.ToString() != "OK") return 21;

      PrintDriveState("moved", carrierAngle, sunAngle, planetSpinAngle, planetX, planetY, planetSpin);

      int operations = Document3D.GetOperations(doc).Count;
      int mates = Document3D.GetMates(doc).Count;
      Console.WriteLine("operations=" + operations);
      Console.WriteLine("nativeMates=" + mates);
      Console.WriteLine("matesMode=parametric_concentric_centers_and_gear_ratio_transforms");
      Console.WriteLine("nativeMateProbe=CompleteError in separate probe, not saved into this model");
      Console.WriteLine("motionDriver=edit external variable CarrierAngle");
      Console.WriteLine("ringFixed=True");
      Console.WriteLine("sunAngleLaw=4*CarrierAngle");
      Console.WriteLine("planetOrbitMode=live_variable_move_centers");
      Console.WriteLine("carrierRotationAppliedToGeometry=False");
      Console.WriteLine("carrierVisibleFrameDeg=45");
      Console.WriteLine("planetSpinLaw=-3.5*CarrierAngle");
      Console.WriteLine("planetSpinAppliedToGeometry=False");
      Console.WriteLine("planetSpinReason=profile_move_plus_rotate_collapses_planet_bbox_in_TFlex17_API");
      Console.WriteLine("planetOrbitRadiusMm=" + Format(planetRadius.RealValue));
      Console.WriteLine("planetGear2DHoles=3");
      Console.WriteLine("planetGearHoleDiameterMm=" + Format(PinDiameter + 0.7));
      Console.WriteLine("hiddenSketchLayerHidden=" + hiddenSketchLayer.Hidden);
      Console.WriteLine("hiddenSketchLayerFrozen=" + hiddenSketchLayer.Frozen);

      bool bodyNull = false;
      bool bboxPositive = true;
      bool planetBodiesVisible = true;
      bool pinBodiesVisible = true;
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
        if (op.Name.StartsWith("planet_", StringComparison.Ordinal)) {
          planetBodiesVisible = planetBodiesVisible && sx > 0.03 && sy > 0.03 && sz > 0.009;
        }
        if (op.Name.StartsWith("pin_", StringComparison.Ordinal)) {
          pinBodiesVisible = pinBodiesVisible && sx > 0.005 && sy > 0.005 && sz > 0.01;
        }
        Console.WriteLine("opBox=" + op.Name + ";bboxValid=" + box.Valid + ";bboxSize=" + Format(sx) + "," + Format(sy) + "," + Format(sz));
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
      Console.WriteLine("planetBodiesVisible=" + planetBodiesVisible);
      Console.WriteLine("pinBodiesVisible=" + pinBodiesVisible);
      Console.WriteLine("bboxMin=" + Format(minX) + "," + Format(minY) + "," + Format(minZ));
      Console.WriteLine("bboxMax=" + Format(maxX) + "," + Format(maxY) + "," + Format(maxZ));
      Console.WriteLine("bboxSpan=" + Format(spanX) + "," + Format(spanY) + "," + Format(spanZ));

      string artifactsDir = Environment.GetEnvironmentVariable("TFLEX_HARNESS_ARTIFACTS_DIR");
      if (!String.IsNullOrWhiteSpace(artifactsDir)) {
        Directory.CreateDirectory(artifactsDir);
        string csv = Path.Combine(artifactsDir, "planetary_motion_frames.csv");
        WriteMotionFrames(csv);
        Console.WriteLine("motionFramesCsv=" + csv);
        Console.WriteLine("motionFramesCsvExists=" + File.Exists(csv));
      }

      bool saved = doc.SaveAs(output);
      Console.WriteLine("saved=" + saved);
      Console.WriteLine("exists=" + File.Exists(output));
      Console.WriteLine("output=" + output);

      double p1RadiusMm = Math.Sqrt(planetX[0].RealValue * planetX[0].RealValue + planetY[0].RealValue * planetY[0].RealValue) * 1000.0;
      if (operations != 9) return 13;
      if (mates != 0) return 14;
      if (bodyNull || !bboxPositive) return 15;
      if (!planetBodiesVisible || !pinBodiesVisible) return 16;
      if (spanX < 0.15 || spanY < 0.15 || spanZ < 0.009) return 24;
      if (Math.Abs(carrierAngle.RealValue - 45.0) > 0.0001) return 17;
      if (Math.Abs(sunAngle.RealValue - 180.0) > 0.0001) return 18;
      if (Math.Abs(planetSpinAngle.RealValue + 157.5) > 0.0001) return 19;
      if (Math.Abs(p1RadiusMm - PlanetCircleRadius) > 0.001) return 22;
      if (!saved || !File.Exists(output)) return 23;
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

  static void PrintDriveState(string label, Variable carrierAngle, Variable sunAngle, Variable planetSpinAngle, Variable[] planetX, Variable[] planetY, Variable[] planetSpin){
    Console.WriteLine(label + ".CarrierAngle=" + Format(carrierAngle.RealValue));
    Console.WriteLine(label + ".SunAngle=" + Format(sunAngle.RealValue));
    Console.WriteLine(label + ".PlanetSpinAngle=" + Format(planetSpinAngle.RealValue));
    for (int i = 0; i < 3; i++) {
      double xMm = planetX[i].RealValue * 1000.0;
      double yMm = planetY[i].RealValue * 1000.0;
      double radiusMm = Math.Sqrt(xMm * xMm + yMm * yMm);
      Console.WriteLine(label + ".P" + (i + 1).ToString(CultureInfo.InvariantCulture) + "_center_mm=" + Format(xMm) + "," + Format(yMm));
      Console.WriteLine(label + ".P" + (i + 1).ToString(CultureInfo.InvariantCulture) + "_radius_mm=" + Format(radiusMm));
      Console.WriteLine(label + ".P" + (i + 1).ToString(CultureInfo.InvariantCulture) + "_spinAngle=" + Format(planetSpin[i].RealValue));
    }
  }

  static ThickenExtrusion MakeProfileBody(Document doc, StandardWorkplane top, string name, List<Point> boundary, double height, int color, List<Point> innerHole, Layer hiddenSketchLayer){
    Area area = new Area(doc);
    AddClosedPolylineContour(doc, area, boundary, true, hiddenSketchLayer);
    if (innerHole != null) {
      AddClosedPolylineContour(doc, area, innerHole, false, hiddenSketchLayer);
    }

    AreaProfile profile = new AreaProfile(doc);
    profile.Name = name + "_profile";
    profile.Area = area;
    profile.WorkSurface = top;
    profile.VisibleInScene = false;

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

  static ThickenExtrusion MakeRingBody(Document doc, StandardWorkplane top, string name, double outerRadius, List<Point> innerBoundary, double height, int color, Layer hiddenSketchLayer){
    Area area = new Area(doc);
    AddClosedPolylineContour(doc, area, BuildCircle(0.0, 0.0, outerRadius, 144), true, hiddenSketchLayer);
    AddClosedPolylineContour(doc, area, innerBoundary, false, hiddenSketchLayer);

    AreaProfile profile = new AreaProfile(doc);
    profile.Name = name + "_profile";
    profile.Area = area;
    profile.WorkSurface = top;
    profile.VisibleInScene = false;

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

  static Cylinder MakeCylinder(Document doc, string name, double diameter, double height, int color){
    Cylinder cylinder = new Cylinder(doc);
    cylinder.Name = name;
    cylinder.Color = color;
    cylinder.Symmetry = true;
    cylinder.Diameter = new Parameter(diameter);
    cylinder.Height = new Parameter(height);
    return cylinder;
  }

  static void AddClosedPolylineContour(Document doc, Area area, List<Point> points, bool direction, Layer hiddenSketchLayer){
    List<Point> closed = new List<Point>(points);
    if (closed.Count == 0) throw new InvalidOperationException("Empty contour");
    Point first = closed[0];
    Point last = closed[closed.Count - 1];
    if (Math.Abs(first.X - last.X) > 1e-9 || Math.Abs(first.Y - last.Y) > 1e-9) {
      closed.Add(new Point(first.X, first.Y));
    }
    PolylineOutline outline = new PolylineOutline(doc, new PolylineGeometry(closed));
    outline.IsService = true;
    if (hiddenSketchLayer != null) {
      outline.Layer = hiddenSketchLayer;
    }
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

  static List<Point> BuildCarrier(double cx, double cy, double phaseRad){
    List<Point> points = new List<Point>();
    for (int i = 0; i < 3; i++) {
      double center = phaseRad + Deg(i * 120.0);
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

  static void AddMove(Object3D obj, string name, double xMm, double yMm, double zMm){
    AddMove(obj, name, new Parameter(MmToModel(xMm)), new Parameter(MmToModel(yMm)), new Parameter(MmToModel(zMm)));
  }

  static void AddMove(Object3D obj, string name, Parameter x, Parameter y, Parameter z){
    TransformationGroup group = obj.Transformations.AddBaseTransfGroup();
    group.Name = name;
    group.AddMoveTransf(TransformationCoordinate.X, x);
    group.AddMoveTransf(TransformationCoordinate.Y, y);
    group.AddMoveTransf(TransformationCoordinate.Z, z);
  }

  static void AddRotateZ(Object3D obj, string name, Variable angle){
    TransformationGroup group = obj.Transformations.AddBaseTransfGroup();
    group.Name = name;
    group.AddRotateTransf(TransformationCoordinate.Z, new Parameter(angle));
  }

  static void WriteMotionFrames(string path){
    List<string> lines = new List<string>();
    lines.Add("CarrierAngleDeg,SunAngleDeg,PlanetSpinDeg,P1Xmm,P1Ymm,P2Xmm,P2Ymm,P3Xmm,P3Ymm");
    double[] frames = new double[] { 0.0, 15.0, 30.0, 45.0, 60.0, 90.0 };
    foreach (double c in frames) {
      double sun = 4.0 * c;
      double spin = -3.5 * c;
      List<string> row = new List<string>();
      row.Add(Format(c));
      row.Add(Format(sun));
      row.Add(Format(spin));
      for (int i = 0; i < 3; i++) {
        double theta = Deg(c + i * 120.0);
        row.Add(Format(PlanetCircleRadius * Math.Cos(theta)));
        row.Add(Format(PlanetCircleRadius * Math.Sin(theta)));
      }
      lines.Add(String.Join(",", row.ToArray()));
    }
    File.WriteAllLines(path, lines.ToArray());
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
