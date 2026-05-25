using System;
using System.Globalization;
using System.IO;
using TFlex;
using TFlex.Model;
using TFlex.Model.Model3D;

public class Program {
  public static int Main(){
    string output = Environment.GetEnvironmentVariable("TFLEX_RECIPE_OUTPUT_FILE");
    if (String.IsNullOrWhiteSpace(output)) output = Path.GetFullPath("crank_yoke_parametric_assembly.grb");
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

      doc.BeginChanges("create parametric crank yoke assembly");
      Variable angle = new Variable(doc, "Angle", 30.0, true);
      Variable r = new Variable(doc, "R", 50.0, true);
      Variable dPin = new Variable(doc, "D_pin", 12.0, true);
      Variable slotWidth = new Variable(doc, "Slot_width", "D_pin + 0.1");
      Variable slotLength = new Variable(doc, "Slot_length", 110.0, true);
      Variable pinX = new Variable(doc, "PinX", "R*cos(Angle)");
      Variable pinY = new Variable(doc, "PinY", "R*sin(Angle)");
      Variable yokeOuterWidth = new Variable(doc, "Yoke_outer_width", 80.0, true);
      Variable yokeOuterLength = new Variable(doc, "Yoke_outer_length", 150.0, true);
      Variable yokeSideWidth = new Variable(doc, "Yoke_side_width", "(Yoke_outer_width - Slot_width) / 2");
      Variable yokeBridgeWidth = new Variable(doc, "Yoke_bridge_width", "(Yoke_outer_length - Slot_length) / 2");
      Variable yokeLeftX = new Variable(doc, "Yoke_left_x", "PinX - (Yoke_outer_width + Slot_width) / 4");
      Variable yokeRightX = new Variable(doc, "Yoke_right_x", "PinX + (Yoke_outer_width + Slot_width) / 4");
      Variable yokeTopY = new Variable(doc, "Yoke_top_y", "(Slot_length + Yoke_bridge_width) / 2");
      Variable yokeBottomY = new Variable(doc, "Yoke_bottom_y", "-Yoke_top_y");
      Variable clearance = new Variable(doc, "Pin_slot_clearance", "Slot_width - D_pin");

      var varsEnd = doc.EndChanges();
      Console.WriteLine("variablesEndChanges=" + varsEnd);
      if (varsEnd.ToString() != "OK") return 12;

      doc.BeginChanges("create parametric crank yoke geometry");
      Block basePlate = MakeBlock(doc, "Base_plate", 260, 180, 10, 0, 0, -6, true);
      Block baseGuideTop = MakeBlock(doc, "Base_guide_top_X", 250, 8, 12, 0, 60, 4, true);
      Block baseGuideBottom = MakeBlock(doc, "Base_guide_bottom_X", 250, 8, 12, 0, -60, 4, true);
      Cylinder baseAxis = MakeCylinder(doc, "Base_crank_axis_Z", 20, 26, 0, 0, 7, true);

      Cylinder crankDisk = MakeCylinder(doc, "Crank_disk_Angle", 110, 8, 0, 0, 4, false);
      AddRotateZ(crankDisk, "Crank rotation Angle", angle);
      Cylinder crankPin = MakeCylinder(doc, "Crank_pin_D_pin", new Parameter(dPin), 26, new Parameter(pinX), new Parameter(pinY), 15, false);

      Block yokeLeft = MakeBlock(doc, "Yoke_left_cheek", new Parameter(yokeSideWidth), new Parameter(slotLength), 16, new Parameter(yokeLeftX), 0, 15, false);
      Block yokeRight = MakeBlock(doc, "Yoke_right_cheek", new Parameter(yokeSideWidth), new Parameter(slotLength), 16, new Parameter(yokeRightX), 0, 15, false);
      Block yokeTop = MakeBlock(doc, "Yoke_top_bridge", new Parameter(yokeOuterWidth), new Parameter(yokeBridgeWidth), 16, new Parameter(pinX), new Parameter(yokeTopY), 15, false);
      Block yokeBottom = MakeBlock(doc, "Yoke_bottom_bridge", new Parameter(yokeOuterWidth), new Parameter(yokeBridgeWidth), 16, new Parameter(pinX), new Parameter(yokeBottomY), 15, false);

      var end = doc.EndChanges();
      Console.WriteLine("endChanges=" + end);
      if (end.ToString() != "OK") return 20;
      Console.WriteLine("Angle=" + Format(angle.RealValue));
      Console.WriteLine("R=" + Format(r.RealValue));
      Console.WriteLine("D_pin=" + Format(dPin.RealValue));
      Console.WriteLine("Slot_width=" + Format(slotWidth.RealValue));
      Console.WriteLine("Slot_length=" + Format(slotLength.RealValue));
      Console.WriteLine("PinX=" + Format(pinX.RealValue));
      Console.WriteLine("PinY=" + Format(pinY.RealValue));
      Console.WriteLine("Pin_slot_clearance=" + Format(clearance.RealValue));
      Console.WriteLine("Base_part_ops=4");
      Console.WriteLine("Crank_part_ops=2");
      Console.WriteLine("Yoke_part_ops=4");
      Console.WriteLine("matesMode=parametric transforms and documented text variables");

      int operationCount = Document3D.GetOperations(doc).Count;
      int mateCount = Document3D.GetMates(doc).Count;
      Console.WriteLine("operations=" + operationCount);
      Console.WriteLine("mates=" + mateCount);
      Console.WriteLine("baseAxisNull=" + (baseAxis.Geometry.Axis == null));
      Console.WriteLine("crankAxisNull=" + (crankDisk.Geometry.Axis == null));
      Console.WriteLine("pinAxisNull=" + (crankPin.Geometry.Axis == null));

      bool bboxPositive = true;
      foreach (Operation op in Document3D.GetOperations(doc)) {
        var box = op.Geometry.AABoundBox;
        double sx = Math.Abs(box.Maximum.X - box.Minimum.X);
        double sy = Math.Abs(box.Maximum.Y - box.Minimum.Y);
        double sz = Math.Abs(box.Maximum.Z - box.Minimum.Z);
        bool positive = box.Valid && sx > 0 && sy > 0 && sz > 0;
        bboxPositive = bboxPositive && positive;
      Console.WriteLine("op=" + op.Name + ";bboxValid=" + box.Valid + ";bboxPositive=" + positive + ";bboxSize=" + Format(sx) + "," + Format(sy) + "," + Format(sz));
      }

      bool saved = doc.SaveAs(output);
      Console.WriteLine("saved=" + saved);
      Console.WriteLine("exists=" + File.Exists(output));
      Console.WriteLine("output=" + output);

      if (operationCount < 10) return 13;
      if (Math.Abs(slotWidth.RealValue - 12.1) > 0.0001) return 14;
      if (Math.Abs(slotLength.RealValue - 110.0) > 0.0001) return 15;
      if (Math.Abs(clearance.RealValue - 0.1) > 0.0001) return 16;
      if (baseAxis.Geometry.Axis == null || crankDisk.Geometry.Axis == null || crankPin.Geometry.Axis == null) return 17;
      if (!bboxPositive) return 18;
      if (!saved || !File.Exists(output)) return 19;
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
    return MakeBlock(doc, name, new Parameter(sx), new Parameter(sy), new Parameter(sz), new Parameter(x), new Parameter(y), new Parameter(z), fixedState);
  }

  static Block MakeBlock(Document doc, string name, Parameter sx, Parameter sy, double sz, Parameter x, Parameter y, double z, bool fixedState){
    return MakeBlock(doc, name, sx, sy, new Parameter(sz), x, y, new Parameter(z), fixedState);
  }

  static Block MakeBlock(Document doc, string name, Parameter sx, Parameter sy, Parameter sz, Parameter x, Parameter y, Parameter z, bool fixedState){
    Block block = new Block(doc);
    block.Name = name;
    block.Cube = false;
    block.Symmetry = true;
    block.XSize = sx;
    block.YSize = sy;
    block.ZSize = sz;
    block.Fixed = fixedState;
    AddMove(block, "position " + name, x, y, z);
    return block;
  }

  static Cylinder MakeCylinder(Document doc, string name, double diameter, double height, double x, double y, double z, bool fixedState){
    return MakeCylinder(doc, name, new Parameter(diameter), new Parameter(height), new Parameter(x), new Parameter(y), new Parameter(z), fixedState);
  }

  static Cylinder MakeCylinder(Document doc, string name, Parameter diameter, double height, Parameter x, Parameter y, double z, bool fixedState){
    return MakeCylinder(doc, name, diameter, new Parameter(height), x, y, new Parameter(z), fixedState);
  }

  static Cylinder MakeCylinder(Document doc, string name, Parameter diameter, Parameter height, Parameter x, Parameter y, Parameter z, bool fixedState){
    Cylinder cylinder = new Cylinder(doc);
    cylinder.Name = name;
    cylinder.Symmetry = true;
    cylinder.Diameter = diameter;
    cylinder.Height = height;
    cylinder.Fixed = fixedState;
    AddMove(cylinder, "position " + name, x, y, z);
    return cylinder;
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

  static string Format(double value){
    return value.ToString("0.########", CultureInfo.InvariantCulture);
  }
}

