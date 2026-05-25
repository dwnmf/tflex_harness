using TFlexEasy;

public class Program {
  public static int Main(){
    using (var sess = EasySession.Start3D()) {
      EasyDiagnostics.Print("helperEnvironmentProbe", true);
    }
    return 0;
  }
}
