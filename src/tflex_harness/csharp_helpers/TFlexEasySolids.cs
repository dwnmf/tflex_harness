using TFlex.Model;
using TFlex.Model.Model3D;

namespace TFlexEasy {
  public static partial class EasySolids {
    public static ThickenExtrusion ExtrudeMm(Document doc, AreaProfile profile, double zMinMm, double heightMm, string name) {
      ThickenExtrusion body = new ThickenExtrusion(doc);
      TrySetName(body, name);
      body.Thickness1 = 0.0;
      body.LengthType = ThickenExtrusion.LengthValue.ValueNo;
      body.ForwardLength = heightMm;
      body.Profile.Add(profile.Geometry.SheetContour);
      if (System.Math.Abs(zMinMm) > 1e-12) EasyPlacement.MoveMm(body, 0.0, 0.0, zMinMm, "z_min_mm");
      EasyDiagnostics.Print(name + ".requestedZMinMm", EasyUnits.F(zMinMm));
      EasyDiagnostics.Print(name + ".requestedHeightMm", EasyUnits.F(heightMm));
      return body;
    }

    public static Cylinder CylinderMm(Document doc, double diameterMm, double zMinMm, double heightMm, string name) {
      Cylinder cylinder = new Cylinder(doc);
      TrySetName(cylinder, name);
      cylinder.Symmetry = false;
      cylinder.Diameter = new Parameter(diameterMm);
      cylinder.Height = new Parameter(heightMm);
      if (System.Math.Abs(zMinMm) > 1e-12) EasyPlacement.MoveMm(cylinder, 0.0, 0.0, zMinMm, "z_min_mm");
      EasyDiagnostics.Print(name + ".requestedDiameterMm", EasyUnits.F(diameterMm));
      EasyDiagnostics.Print(name + ".requestedZMinMm", EasyUnits.F(zMinMm));
      EasyDiagnostics.Print(name + ".requestedHeightMm", EasyUnits.F(heightMm));
      return cylinder;
    }

    public static Block BlockMm(Document doc, double sxMm, double syMm, double szMm, double xMm, double yMm, double zMm, string name) {
      return BlockMm(doc, sxMm, syMm, szMm, xMm, yMm, zMm, name, true);
    }

    public static Block BlockMm(Document doc, double sxMm, double syMm, double szMm, double xMm, double yMm, double zMm, string name, bool symmetry) {
      Block block = new Block(doc);
      TrySetName(block, name);
      block.Cube = false;
      block.Symmetry = symmetry;
      block.XSize = new Parameter(sxMm);
      block.YSize = new Parameter(syMm);
      block.ZSize = new Parameter(szMm);
      EasyPlacement.MoveMm(block, xMm, yMm, zMm, "place_" + name);
      EasyDiagnostics.Print(name + ".requestedSizeMm", EasyUnits.F(sxMm) + "," + EasyUnits.F(syMm) + "," + EasyUnits.F(szMm));
      EasyDiagnostics.Print(name + ".requestedCenterMm", EasyUnits.F(xMm) + "," + EasyUnits.F(yMm) + "," + EasyUnits.F(zMm));
      return block;
    }

    public static Cylinder CylinderMm(Document doc, double diameterMm, double heightMm, double xMm, double yMm, double zMm, string axis, string name) {
      Cylinder cylinder = new Cylinder(doc);
      TrySetName(cylinder, name);
      cylinder.Symmetry = true;
      cylinder.Diameter = new Parameter(diameterMm);
      cylinder.Height = new Parameter(heightMm / 2.0);
      string normalized = (axis ?? "Z").Trim().ToUpperInvariant();
      EasyPlacement.MoveMm(cylinder, xMm, yMm, zMm, "place_" + name);
      if (normalized == "X") RotateYDeg(cylinder, 90.0, "axis_x_" + name);
      else if (normalized == "Y") RotateXDeg(cylinder, 90.0, "axis_y_" + name);
      else if (normalized != "Z") throw new System.ArgumentException("axis must be X, Y, or Z", "axis");
      EasyDiagnostics.Print(name + ".requestedDiameterMm", EasyUnits.F(diameterMm));
      EasyDiagnostics.Print(name + ".requestedHeightMm", EasyUnits.F(heightMm));
      EasyDiagnostics.Print(name + ".requestedAxis", normalized);
      EasyDiagnostics.Print(name + ".requestedCenterMm", EasyUnits.F(xMm) + "," + EasyUnits.F(yMm) + "," + EasyUnits.F(zMm));
      return cylinder;
    }

    public static ThickenExtrusion ExtrudeOn(Document doc, AreaProfile profile, StandardWorkplane workplane, double heightMm, string name) {
      profile.WorkSurface = workplane;
      return ExtrudeMm(doc, profile, 0.0, heightMm, name);
    }

    public static Cylinder CutCylinderThrough(Document doc, double diameterMm, double lengthMm, double xMm, double yMm, double zMm, string axis, string name) {
      Cylinder cutter = CylinderMm(doc, diameterMm, lengthMm, xMm, yMm, zMm, axis, name);
      EasyDiagnostics.Print(name + ".cutter", true);
      return cutter;
    }

    public static Operation NamedCutter(Operation op, string name) {
      if (op != null) TrySetName(op, name);
      EasyDiagnostics.Print(name + ".cutter", true);
      return op;
    }

    static void RotateXDeg(Object3D obj, double angleDeg, string name) {
      TransformationGroup group = obj.Transformations.AddBaseTransfGroup();
      group.Name = name;
      group.AddRotateTransf(TransformationCoordinate.X, new Parameter(angleDeg));
    }

    static void RotateYDeg(Object3D obj, double angleDeg, string name) {
      TransformationGroup group = obj.Transformations.AddBaseTransfGroup();
      group.Name = name;
      group.AddRotateTransf(TransformationCoordinate.Y, new Parameter(angleDeg));
    }

    static void TrySetName(Object3D obj, string name) {
      try { obj.Name = name; }
      catch (System.Exception ex) { EasyDiagnostics.Print(name + ".nameSetError", ex.GetType().Name + ": " + ex.Message); }
    }
  }
}
