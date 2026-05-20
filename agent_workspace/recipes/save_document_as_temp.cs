using System;
using System.IO;
using TFlex;
using TFlex.Model;

public class Program {
  public static int Main(){
    string output = Environment.GetEnvironmentVariable("TFLEX_RECIPE_OUTPUT_FILE");
    if (String.IsNullOrWhiteSpace(output)) output = Path.GetFullPath("saved_document_as_temp.grb");
    Directory.CreateDirectory(Path.GetDirectoryName(output));

    var setup = new ApplicationSessionSetup();
    setup.ReadOnly = false;
    setup.Enable3D = false;
    setup.EnableDOCs = false;
    setup.EnableMacros = false;
    setup.PromptToSaveModifiedDocuments = false;
    setup.ProtectionLicense = ApplicationSessionSetup.License.TFlexAPI;

    bool init = Application.InitSession(setup);
    Console.WriteLine("init=" + init);
    if (!init) return 10;

    Document document = null;
    try {
      document = Application.NewDocument(false, false);
      Console.WriteLine("docNull=" + (document == null));
      if (document == null) return 11;

      Console.WriteLine("titleBefore=" + document.Title);
      Console.WriteLine("fileNameBefore=" + document.FileName);

      bool saved = document.SaveAs(output);
      Console.WriteLine("saved=" + saved);
      Console.WriteLine("exists=" + File.Exists(output));
      Console.WriteLine("output=" + output);
      Console.WriteLine("titleAfter=" + document.Title);
      Console.WriteLine("fileNameAfter=" + document.FileName);
      Console.WriteLine("filePathAfter=" + document.FilePath);

      string artifactsDir = Environment.GetEnvironmentVariable("TFLEX_HARNESS_ARTIFACTS_DIR");
      if (!String.IsNullOrWhiteSpace(artifactsDir)) {
        Directory.CreateDirectory(artifactsDir);
        string marker = Path.Combine(artifactsDir, "saved_document_path.txt");
        File.WriteAllText(marker, output);
        Console.WriteLine("artifactMarker=" + marker);
      }

      if (!saved || !File.Exists(output)) return 12;
      if (String.IsNullOrWhiteSpace(document.FileName)) return 13;
      return 0;
    } catch (Exception ex) {
      Console.WriteLine("exceptionType=" + ex.GetType().FullName);
      Console.WriteLine("exception=" + ex.Message);
      Console.WriteLine(ex.ToString());
      return 99;
    } finally {
      try { if (document != null) document.Close(); } catch (Exception closeEx) { Console.WriteLine("closeException=" + closeEx.Message); }
      if (Application.IsSessionInitialized) Application.ExitSession();
      Console.WriteLine("session=" + Application.IsSessionInitialized);
    }
  }
}
