using TFlex.Model;
using TFlex.Model.Model3D;

namespace TFlexEasy {
  public struct EasyPoint2 {
    public double XMm;
    public double YMm;

    public EasyPoint2(double xMm, double yMm) {
      XMm = xMm;
      YMm = yMm;
    }
  }

  public static class EasyPlacement {
    public static EasyPoint2 PolarMm(double radiusMm, double angleDeg) {
      double angle = EasyUnits.DegToRad(angleDeg);
      return new EasyPoint2(radiusMm * System.Math.Cos(angle), radiusMm * System.Math.Sin(angle));
    }

    public static void MoveMm(Object3D obj, double xMm, double yMm, double zMm, string name) {
      TransformationGroup group = obj.Transformations.AddBaseTransfGroup();
      group.Name = name;
      group.AddMoveTransf(TransformationCoordinate.X, new Parameter(EasyUnits.MmToModel(xMm)));
      group.AddMoveTransf(TransformationCoordinate.Y, new Parameter(EasyUnits.MmToModel(yMm)));
      group.AddMoveTransf(TransformationCoordinate.Z, new Parameter(EasyUnits.MmToModel(zMm)));
    }

    public static void MoveMm(Object3D obj, double xMm, double yMm, double zMm) {
      MoveMm(obj, xMm, yMm, zMm, "move_mm");
    }

    public static void RotateZDeg(Object3D obj, double angleDeg, string name) {
      TransformationGroup group = obj.Transformations.AddBaseTransfGroup();
      group.Name = name;
      group.AddRotateTransf(TransformationCoordinate.Z, new Parameter(angleDeg));
    }

    public static void RotateZDeg(Object3D obj, double angleDeg) {
      RotateZDeg(obj, angleDeg, "rotate_z_deg");
    }
  }
}
