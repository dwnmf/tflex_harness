using TFlex.Model;
using TFlex.Model.Model3D;
using TFlexEasy;

public class Program {
  public static int Main(){
    using (var sess = EasySession.Start3D()) {
      var doc = sess.New3DDocument(false);
      doc.BeginChanges("helper step export recipe");
      var profile = EasyProfiles.Circle(doc, 20.0, "circle20");
      var body = EasySolids.ExtrudeMm(doc, profile, 0.0, 8.0, "helper_cylinder20x8");
      var end = doc.EndChanges();
      EasyDiagnostics.Print("endChanges", end);
      EasyDiagnostics.PrintBodyBoxMm("helper_cylinder20x8", body);
      if (end.ToString() != "OK") return 10;
      bool step = EasyExport.Step(doc, sess.ArtifactPath("helper_simple.step"));
      return step ? 0 : 30;
    }
  }
}
