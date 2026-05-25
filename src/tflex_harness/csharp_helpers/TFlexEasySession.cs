using System;
using System.Collections.Generic;
using System.IO;
using TFlex;
using TFlex.Model;

namespace TFlexEasy {
  public sealed class EasySession : IDisposable {
    readonly List<Document> documents = new List<Document>();
    readonly string artifactsDir;
    bool disposed;

    EasySession(string artifactsDir) {
      this.artifactsDir = artifactsDir;
    }

    public static EasySession Start3D() {
      return Start(enable3D: true);
    }

    public static EasySession Start2D() {
      return Start(enable3D: false);
    }

    static EasySession Start(bool enable3D) {
      var setup = new ApplicationSessionSetup();
      setup.ReadOnly = false;
      setup.Enable3D = enable3D;
      setup.EnableDOCs = false;
      setup.EnableMacros = false;
      setup.PromptToSaveModifiedDocuments = false;
      setup.ProtectionLicense = ApplicationSessionSetup.License.TFlex3D;
      bool init = Application.InitSession(setup);
      EasyDiagnostics.Print("easy.init", init);
      if (!init) throw new InvalidOperationException("Application.InitSession returned false");
      string dir = Environment.GetEnvironmentVariable("TFLEX_HARNESS_ARTIFACTS_DIR");
      if (String.IsNullOrWhiteSpace(dir)) dir = Environment.GetEnvironmentVariable("TFLEX_HARNESS_RUN_DIR");
      if (String.IsNullOrWhiteSpace(dir)) dir = Directory.GetCurrentDirectory();
      Directory.CreateDirectory(dir);
      return new EasySession(dir);
    }

    public Document New3DDocument(bool visible) {
      Document doc = Application.NewDocument(true, visible);
      EasyDiagnostics.Print("easy.docNull", doc == null);
      if (doc == null) throw new InvalidOperationException("Application.NewDocument(true, visible) returned null");
      documents.Add(doc);
      return doc;
    }

    public Document New2DDocument(bool visible) {
      Document doc = Application.NewDocument(false, visible);
      EasyDiagnostics.Print("easy.docNull", doc == null);
      if (doc == null) throw new InvalidOperationException("Application.NewDocument(false, visible) returned null");
      documents.Add(doc);
      return doc;
    }

    public string ArtifactPath(string fileName) {
      string safeName = Path.GetFileName(fileName);
      if (String.IsNullOrWhiteSpace(safeName)) throw new ArgumentException("fileName must include a file name", "fileName");
      Directory.CreateDirectory(artifactsDir);
      return Path.Combine(artifactsDir, safeName);
    }

    public void Dispose() {
      if (disposed) return;
      disposed = true;
      for (int i = documents.Count - 1; i >= 0; i--) {
        try {
          if (documents[i] != null) documents[i].Close();
        } catch (Exception ex) {
          EasyDiagnostics.Print("easy.closeException", ex.Message);
        }
      }
      if (Application.IsSessionInitialized) Application.ExitSession();
      EasyDiagnostics.Print("easy.session", Application.IsSessionInitialized);
    }
  }
}
