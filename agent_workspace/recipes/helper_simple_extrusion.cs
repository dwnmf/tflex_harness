using TFlex.Model;
using TFlex.Model.Model3D;
using TFlexEasy;

public class Program {
  public static int Main(){
    using (var sess = EasySession.Start3D()) {
      var doc = sess.New3DDocument(false);
      doc.BeginChanges("helper simple extrusion recipe");
      var profile = EasyProfiles.Circle(doc, 20.0, "circle20");
      var body = EasySolids.ExtrudeMm(doc, profile, 0.0, 8.0, "helper_cylinder20x8");
      var end = doc.EndChanges();
      EasyDiagnostics.Print("endChanges", end);
      EasyDiagnostics.Print("operations", Document3D.GetOperations(doc).Count);
      BodyBoxMm box = EasyDiagnostics.PrintBodyBoxMm("helper_cylinder20x8", body);
      if (end.ToString() != "OK") return 10;
      if (!box.Valid) return 11;
      if (!EasyDiagnostics.Near(box.SpanX, 20.0, 0.1) || !EasyDiagnostics.Near(box.SpanY, 20.0, 0.1) || !EasyDiagnostics.Near(box.SpanZ, 8.0, 0.1)) return 12;
      bool saved = EasyExport.Grb(doc, sess.ArtifactPath("helper_simple_extrusion.grb"));
      return saved ? 0 : 20;
    }
  }
}
