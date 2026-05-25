using System.IO;
using TFlex.Model;

namespace TFlexEasy {
  public static class EasyExport {
    public static bool Grb(Document doc, string path) {
      string dir = Path.GetDirectoryName(path);
      if (!System.String.IsNullOrWhiteSpace(dir)) Directory.CreateDirectory(dir);
      bool ok = doc.SaveAs(path);
      EasyDiagnostics.Print("easy.grbSaved", ok);
      EasyDiagnostics.Print("easy.grbExists", File.Exists(path));
      EasyDiagnostics.Print("easy.grbPath", path);
      return ok && File.Exists(path);
    }

    public static bool Step(Document doc, string path) {
      string dir = Path.GetDirectoryName(path);
      if (!System.String.IsNullOrWhiteSpace(dir)) Directory.CreateDirectory(dir);
      var exporter = doc.ExportToSTEP;
      bool exportResult = exporter.Export(path);
      bool exists = File.Exists(path);
      long size = exists ? new FileInfo(path).Length : 0;
      bool ok = exists && size > 0;
      EasyDiagnostics.Print("easy.stepExportResult", exportResult);
      EasyDiagnostics.Print("easy.stepSaved", ok);
      EasyDiagnostics.Print("easy.stepExists", exists);
      EasyDiagnostics.Print("easy.stepPath", path);
      if (exists) EasyDiagnostics.Print("easy.stepSize", size);
      return ok;
    }

    public static bool Pdf(Document doc, string path) {
      string dir = Path.GetDirectoryName(path);
      if (!System.String.IsNullOrWhiteSpace(dir)) Directory.CreateDirectory(dir);
      EnsurePdfExportModule();
      var exporter = new ExportToPDF(doc);
      exporter.OpenExportFile = false;
      exporter.IsSelectPagesDialogEnabled = false;
      bool exportResult = exporter.Export(path);
      bool exists = File.Exists(path);
      long size = exists ? new FileInfo(path).Length : 0;
      bool ok = exists && size > 0;
      EasyDiagnostics.Print("easy.pdfExportResult", exportResult);
      EasyDiagnostics.Print("easy.pdfSaved", ok);
      EasyDiagnostics.Print("easy.pdfExists", exists);
      EasyDiagnostics.Print("easy.pdfPath", path);
      if (exists) EasyDiagnostics.Print("easy.pdfSize", size);
      return ok;
    }

    static void EnsurePdfExportModule() {
      try {
        string target = Path.Combine(Directory.GetCurrentDirectory(), "PDFExport.dll");
        string source = FindModule("PDFExport.dll", target);
        EasyDiagnostics.Print("easy.pdfModuleSource", source);
        EasyDiagnostics.Print("easy.pdfModuleSourceExists", File.Exists(source));
        if (File.Exists(source) && !File.Exists(target)) File.Copy(source, target, true);
        EasyDiagnostics.Print("easy.pdfModuleLocalExists", File.Exists(target));
      } catch (System.Exception ex) {
        EasyDiagnostics.Print("easy.pdfModuleCopyError", ex.Message);
      }
    }

    static string FindModule(string fileName, string excludedPath) {
      string current = Path.Combine(Directory.GetCurrentDirectory(), fileName);
      if (File.Exists(current)) return current;
      string assemblyDir = Path.GetDirectoryName(typeof(Document).Assembly.Location);
      string fromAssembly = Path.Combine(assemblyDir, fileName);
      if (File.Exists(fromAssembly) && !SamePath(fromAssembly, excludedPath)) return fromAssembly;
      string path = System.Environment.GetEnvironmentVariable("PATH") ?? "";
      foreach (string item in path.Split(Path.PathSeparator)) {
        if (System.String.IsNullOrWhiteSpace(item)) continue;
        string candidate = Path.Combine(item, fileName);
        if (File.Exists(candidate) && !SamePath(candidate, excludedPath)) return candidate;
      }
      return fromAssembly;
    }

    static bool SamePath(string a, string b) {
      return System.String.Equals(Path.GetFullPath(a), Path.GetFullPath(b), System.StringComparison.OrdinalIgnoreCase);
    }
  }
}
