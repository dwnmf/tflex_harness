using System;
using System.Collections.Generic;
using TFlex.Model;
using TFlex.Model.Model3D;

namespace TFlexEasy {
  public static class EasyFeatures {
    public static ThickenExtrusion BasePlate(Document doc, double sxMm, double syMm, double heightMm, double cornerRadiusMm, string name) {
      AreaProfile profile = EasyProfiles.RoundedRectangle(doc, 0.0, 0.0, sxMm, syMm, cornerRadiusMm, name + "_profile");
      ThickenExtrusion plate = EasySolids.ExtrudeOn(doc, profile, EasyWorkplanes.Top(doc), heightMm, name);
      EasyDiagnostics.Print(name + ".feature", "base_plate");
      EasyDiagnostics.Print(name + ".roundedCornerRadiusMm", EasyUnits.F(cornerRadiusMm));
      return plate;
    }

    public static Operation[] ClevisLugPair(Document doc, double radiusMm, double bottomZMm, double centerZMm, double thicknessMm, double gapMm, string name) {
      AreaProfile profileA = EasyProfiles.LugProfile(doc, radiusMm, bottomZMm, centerZMm, name + "_positive_profile");
      ThickenExtrusion positive = EasySolids.ExtrudeOn(doc, profileA, EasyWorkplanes.Front(doc), thicknessMm, name + "_positive");
      EasyPlacement.MoveMm(positive, 0.0, gapMm / 2.0 + thicknessMm, 0.0, "place_" + name + "_positive");
      AreaProfile profileB = EasyProfiles.LugProfile(doc, radiusMm, bottomZMm, centerZMm, name + "_negative_profile");
      ThickenExtrusion negative = EasySolids.ExtrudeOn(doc, profileB, EasyWorkplanes.Front(doc), thicknessMm, name + "_negative");
      EasyPlacement.MoveMm(negative, 0.0, -(gapMm / 2.0), 0.0, "place_" + name + "_negative");
      EasyDiagnostics.Print(name + ".feature", "clevis_lug_pair");
      EasyDiagnostics.Print(name + ".lugCount", 2);
      return new Operation[] { positive, negative };
    }

    public static Operation[] MountingHolePattern(Document doc, double[] xMm, double[] yMm, double diameterMm, double lengthMm, string name) {
      List<Operation> cutters = new List<Operation>();
      foreach (double x in xMm) {
        foreach (double y in yMm) {
          cutters.Add(EasySolids.CutCylinderThrough(doc, diameterMm, lengthMm, x, y, 0.0, "Z", name + "_" + Safe(x) + "_" + Safe(y)));
        }
      }
      EasyDiagnostics.Print(name + ".feature", "mounting_hole_pattern");
      EasyDiagnostics.Print(name + ".holeCount", cutters.Count);
      return cutters.ToArray();
    }

    public static Operation HorizontalBoreCutter(Document doc, double diameterMm, double lengthMm, double xMm, double yMm, double zMm, string name) {
      Operation cutter = EasySolids.CutCylinderThrough(doc, diameterMm, lengthMm, xMm, yMm, zMm, "Y", name);
      EasyDiagnostics.Print(name + ".feature", "horizontal_bore_cutter");
      return cutter;
    }

    public static Operation TriangularLighteningCutout(Document doc, EasyPoint2 p1, EasyPoint2 p2, EasyPoint2 p3, double lengthMm, double yCenterMm, string name) {
      AreaProfile profile = EasyProfiles.Triangle(doc, p1, p2, p3, name + "_profile");
      ThickenExtrusion cutter = EasySolids.ExtrudeOn(doc, profile, EasyWorkplanes.Front(doc), lengthMm, name);
      EasyPlacement.MoveMm(cutter, 0.0, yCenterMm, 0.0, "place_" + name);
      EasyDiagnostics.Print(name + ".feature", "triangular_lightening_cutout");
      return cutter;
    }

    public static Operation ReinforcingRib(Document doc, EasyPoint2 p1, EasyPoint2 p2, EasyPoint2 p3, double thicknessMm, double yStartMm, string name) {
      AreaProfile profile = EasyProfiles.Triangle(doc, p1, p2, p3, name + "_profile");
      ThickenExtrusion rib = EasySolids.ExtrudeOn(doc, profile, EasyWorkplanes.Front(doc), thicknessMm, name);
      EasyPlacement.MoveMm(rib, 0.0, yStartMm, 0.0, "place_" + name);
      EasyDiagnostics.Print(name + ".feature", "reinforcing_rib");
      return rib;
    }

    public static BooleanOperation RoundTransitionBlend(BooleanOperation op, double radiusMm) {
      EasyDiagnostics.Print(op.Name + ".feature", "round_transition_blend");
      return EasyBoolean.WithBlend(op, radiusMm);
    }

    static string Safe(double value) {
      return EasyUnits.F(value).Replace("-", "m").Replace(".", "_");
    }
  }
}
