using System;
using TFlex;

public class Program {
  public static int Main(){
    var setup = new ApplicationSessionSetup();
    setup.ReadOnly = true;
    setup.Enable3D = false;
    setup.EnableDOCs = false;
    setup.EnableMacros = false;
    setup.PromptToSaveModifiedDocuments = false;
    setup.ProtectionLicense = ApplicationSessionSetup.License.TFlexAPI;
    Console.WriteLine("before=" + Application.IsSessionInitialized);
    bool ok = Application.InitSession(setup);
    Console.WriteLine("init=" + ok);
    Console.WriteLine("after=" + Application.IsSessionInitialized);
    if (Application.IsSessionInitialized) Application.ExitSession();
    Console.WriteLine("exited=" + Application.IsSessionInitialized);
    return ok ? 0 : 3;
  }
}
