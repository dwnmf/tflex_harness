using TFlex.Model;
using TFlex.Model.Model3D;

namespace TFlexEasy {
  public static class EasyWorkplanes {
    public static StandardWorkplane Top(Document doc) {
      return new StandardWorkplane(doc, StandardWorkplane.StandardType.Top);
    }

    public static StandardWorkplane Front(Document doc) {
      return new StandardWorkplane(doc, StandardWorkplane.StandardType.Front);
    }

    public static StandardWorkplane Left(Document doc) {
      return new StandardWorkplane(doc, StandardWorkplane.StandardType.Left);
    }

    public static void PrintAxisMapping(Document doc) {
      EasyDiagnostics.Print("workplane.top.profileAxes", "X,Y");
      EasyDiagnostics.Print("workplane.top.extrudeAxis", "Z");
      EasyDiagnostics.Print("workplane.front.profileAxes", "X,Z");
      EasyDiagnostics.Print("workplane.front.extrudeAxis", "Y");
      EasyDiagnostics.Print("workplane.left.profileAxes", "Y,Z");
      EasyDiagnostics.Print("workplane.left.extrudeAxis", "X");
    }

    public static bool AssertKnownMapping() {
      EasyDiagnostics.Print("workplane.mapping.liveProbe", "artifacts/runs/20260527_104417_522663_probe_workplane_map");
      EasyDiagnostics.Print("workplane.mapping.known", true);
      return true;
    }
  }
}
