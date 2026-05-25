using TFlex.Model;
using TFlex.Model.Model3D;

namespace TFlexEasy {
  public static class EasySolids {
    public static ThickenExtrusion ExtrudeMm(Document doc, AreaProfile profile, double zMinMm, double heightMm, string name) {
      ThickenExtrusion body = new ThickenExtrusion(doc);
      body.Name = name;
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
      cylinder.Name = name;
      cylinder.Symmetry = false;
      cylinder.Diameter = new Parameter(diameterMm);
      cylinder.Height = new Parameter(heightMm);
      if (System.Math.Abs(zMinMm) > 1e-12) EasyPlacement.MoveMm(cylinder, 0.0, 0.0, zMinMm, "z_min_mm");
      EasyDiagnostics.Print(name + ".requestedDiameterMm", EasyUnits.F(diameterMm));
      EasyDiagnostics.Print(name + ".requestedZMinMm", EasyUnits.F(zMinMm));
      EasyDiagnostics.Print(name + ".requestedHeightMm", EasyUnits.F(heightMm));
      return cylinder;
    }
  }
}
