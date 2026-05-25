using System;
using System.Globalization;
using System.IO;
using TFlex;
using TFlex.Model;
using TFlex.Model.Model3D;

public class Program {
  const int Steps = 24;
  const double AngleStep = 22.5;
  const double Rise = 12.0;
  const double TreadDepth = 145.0;
  const double TreadWidth = 48.0;
  const double TreadThickness = 7.0;
  const double TreadRadius = 88.0;
  const double ColumnDiameter = 32.0;
  const double OuterRadius = 165.0;

  public static int Main(){
    string output = Environment.GetEnvironmentVariable("TFLEX_RECIPE_OUTPUT_FILE");
    if (String.IsNullOrWhiteSpace(output)) output = Path.GetFullPath("spiral_staircase.grb");
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

      doc.BeginChanges("create spiral staircase geometry");

      double totalHeight = (Steps - 1) * Rise + 45.0;
      MakeCylinder(doc, "central_column", ColumnDiameter, totalHeight, 0, 0, totalHeight / 2.0 - 2.0, true);
      MakeCylinder(doc, "round_base_plate", 250.0, 8.0, 0, 0, -4.0, true);
      MakeCylinder(doc, "top_landing_plate", 210.0, 8.0, 0, 0, (Steps - 1) * Rise + 8.0, false);

      for (int i = 0; i < Steps; i++) {
        double angle = i * AngleStep;
        double radians = angle * Math.PI / 180.0;
        double z = i * Rise;
        double cx = TreadRadius * Math.Cos(radians);
        double cy = TreadRadius * Math.Sin(radians);
        double ox = OuterRadius * Math.Cos(radians);
        double oy = OuterRadius * Math.Sin(radians);

        Block tread = MakeBlock(doc, "tread_" + (i + 1).ToString("00"), TreadDepth, TreadWidth, TreadThickness, cx, cy, z, false);
        AddRotateZ(tread, "orient tread " + (i + 1).ToString("00"), angle);

        Cylinder baluster = MakeCylinder(doc, "outer_baluster_" + (i + 1).ToString("00"), 8.0, 56.0, ox, oy, z + 28.0, false);
        Block rail = MakeBlock(doc, "handrail_segment_" + (i + 1).ToString("00"), 44.0, 9.0, 9.0, ox, oy, z + 58.0, false);
        AddRotateZ(rail, "orient rail " + (i + 1).ToString("00"), angle + 90.0);
      }

      var end = doc.EndChanges();
      Console.WriteLine("endChanges=" + end);
      if (end.ToString() != "OK") return 12;

      int operations = Document3D.GetOperations(doc).Count;
      int mates = Document3D.GetMates(doc).Count;
      Console.WriteLine("steps=" + Steps);
      Console.WriteLine("angleStep=" + Format(AngleStep));
      Console.WriteLine("rise=" + Format(Rise));
      Console.WriteLine("totalHeight=" + Format(totalHeight));
      Console.WriteLine("operations=" + operations);
      Console.WriteLine("mates=" + mates);

      bool bboxPositive = true;
      double minX = Double.PositiveInfinity;
      double minY = Double.PositiveInfinity;
      double minZ = Double.PositiveInfinity;
      double maxX = Double.NegativeInfinity;
      double maxY = Double.NegativeInfinity;
      double maxZ = Double.NegativeInfinity;
      foreach (Operation op in Document3D.GetOperations(doc)) {
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
      Console.WriteLine("bboxPositive=" + bboxPositive);
      Console.WriteLine("bboxMin=" + Format(minX) + "," + Format(minY) + "," + Format(minZ));
      Console.WriteLine("bboxMax=" + Format(maxX) + "," + Format(maxY) + "," + Format(maxZ));
      Console.WriteLine("bboxSpan=" + Format(spanX) + "," + Format(spanY) + "," + Format(spanZ));

      bool saved = doc.SaveAs(output);
      Console.WriteLine("saved=" + saved);
      Console.WriteLine("exists=" + File.Exists(output));
      Console.WriteLine("output=" + output);

      if (operations < (3 + Steps * 3)) return 13;
      if (!bboxPositive) return 14;
      if (spanX < 250 || spanY < 250 || spanZ < 250) return 15;
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

  static Block MakeBlock(Document doc, string name, double sx, double sy, double sz, double x, double y, double z, bool fixedState){
    Block block = new Block(doc);
    block.Name = name;
    block.Cube = false;
    block.Symmetry = true;
    block.XSize = new Parameter(sx);
    block.YSize = new Parameter(sy);
    block.ZSize = new Parameter(sz);
    block.Fixed = fixedState;
    AddMove(block, "position " + name, x, y, z);
    return block;
  }

  static Cylinder MakeCylinder(Document doc, string name, double diameter, double height, double x, double y, double z, bool fixedState){
    Cylinder cylinder = new Cylinder(doc);
    cylinder.Name = name;
    cylinder.Symmetry = true;
    cylinder.Diameter = new Parameter(diameter);
    cylinder.Height = new Parameter(height);
    cylinder.Fixed = fixedState;
    AddMove(cylinder, "position " + name, x, y, z);
    return cylinder;
  }

  static void AddMove(Object3D obj, string name, double x, double y, double z){
    TransformationGroup group = obj.Transformations.AddBaseTransfGroup();
    group.Name = name;
    group.AddMoveTransf(TransformationCoordinate.X, new Parameter(x));
    group.AddMoveTransf(TransformationCoordinate.Y, new Parameter(y));
    group.AddMoveTransf(TransformationCoordinate.Z, new Parameter(z));
  }

  static void AddRotateZ(Object3D obj, string name, double angle){
    TransformationGroup group = obj.Transformations.AddBaseTransfGroup();
    group.Name = name;
    group.AddRotateTransf(TransformationCoordinate.Z, new Parameter(angle));
  }

  static string Format(double value){
    return value.ToString("0.########", CultureInfo.InvariantCulture);
  }
}
