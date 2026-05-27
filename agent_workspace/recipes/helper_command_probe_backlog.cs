using TFlex.Model;
using TFlexEasy;

public class Program {
  public static int Main(){
    using (var sess = EasySession.Start3D()) {
      var doc = sess.New3DDocument(false);
      string[] names = EasyCommandProbe.ListKnownCommands();
      var zoom = EasyCommandProbe.TryRunSystemCommand("ZoomMax", new ModelObject[0]);
      var createMate = EasyCommandProbe.TryRunSystemCommand("CreateMate", new ModelObject[0]);
      bool listOk = names.Length > 0;
      bool zoomOk = zoom.Started && zoom.Error == null;
      bool createMateRejected = !createMate.Started && createMate.Error != null;
      EasyDiagnostics.Print("commandRecipe.listOk", listOk);
      EasyDiagnostics.Print("commandRecipe.zoomMaxOk", zoomOk);
      EasyDiagnostics.Print("commandRecipe.createMateRejected", createMateRejected);
      bool ok = listOk && zoomOk && createMateRejected;
      EasyDiagnostics.Print("commandRecipe.expectedClean", ok);
      return ok ? 0 : 10;
    }
  }
}
