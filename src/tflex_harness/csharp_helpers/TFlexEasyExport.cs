using System.IO;
using System.Collections.Generic;
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

    public static bool Dxf(Document doc, string path) {
      string dir = Path.GetDirectoryName(path);
      if (!System.String.IsNullOrWhiteSpace(dir)) Directory.CreateDirectory(dir);
      var exporter = doc.ExportToDXF;
      bool exportResult = exporter.Export(path);
      bool exists = File.Exists(path);
      long size = exists ? new FileInfo(path).Length : 0;
      bool ok = exists && size > 0;
      EasyDiagnostics.Print("easy.dxfExportResult", exportResult);
      EasyDiagnostics.Print("easy.dxfSaved", ok);
      EasyDiagnostics.Print("easy.dxfExists", exists);
      EasyDiagnostics.Print("easy.dxfPath", path);
      if (exists) EasyDiagnostics.Print("easy.dxfSize", size);
      return ok;
    }

    public static bool Dwg(Document doc, string path) {
      string dir = Path.GetDirectoryName(path);
      if (!System.String.IsNullOrWhiteSpace(dir)) Directory.CreateDirectory(dir);
      var exporter = doc.ExportToDWG;
      bool exportResult = exporter.Export(path);
      bool exists = File.Exists(path);
      long size = exists ? new FileInfo(path).Length : 0;
      bool ok = exists && size > 0;
      EasyDiagnostics.Print("easy.dwgExportResult", exportResult);
      EasyDiagnostics.Print("easy.dwgSaved", ok);
      EasyDiagnostics.Print("easy.dwgExists", exists);
      EasyDiagnostics.Print("easy.dwgPath", path);
      if (exists) EasyDiagnostics.Print("easy.dwgSize", size);
      return ok;
    }

    public static bool All(Document doc, string basePath, bool grb = true, bool step = true, bool dxf = false, bool dwg = false, bool pdf = false) {
      bool ok = true;
      Dictionary<string, string> manifest = new Dictionary<string, string>();
      manifest["basePath"] = basePath;
      if (grb) {
        string path = basePath + ".grb";
        bool saved = Grb(doc, path);
        manifest["grb"] = saved.ToString();
        manifest["grbPath"] = path;
        ok = ok && saved;
      }
      if (step) {
        string path = basePath + ".stp";
        bool saved = Step(doc, path);
        manifest["step"] = saved.ToString();
        manifest["stepPath"] = path;
        ok = ok && saved;
      }
      if (dxf) {
        string path = basePath + ".dxf";
        bool saved = Dxf(doc, path);
        manifest["dxf"] = saved.ToString();
        manifest["dxfPath"] = path;
        ok = ok && saved;
      }
      if (dwg) {
        string path = basePath + ".dwg";
        bool saved = Dwg(doc, path);
        manifest["dwg"] = saved.ToString();
        manifest["dwgPath"] = path;
        ok = ok && saved;
      }
      if (pdf) {
        string path = basePath + ".pdf";
        bool saved = Pdf(doc, path);
        manifest["pdf"] = saved.ToString();
        manifest["pdfPath"] = path;
        ok = ok && saved;
      }
      manifest["ok"] = ok.ToString();
      ExportManifest(basePath + ".export_manifest.json", manifest);
      return ok;
    }

    public static bool VerifyNonEmpty(string path) {
      bool exists = File.Exists(path);
      long size = exists ? new FileInfo(path).Length : 0;
      bool ok = exists && size > 0;
      EasyDiagnostics.Print("easy.export.verifyPath", path);
      EasyDiagnostics.Print("easy.export.verifyExists", exists);
      EasyDiagnostics.Print("easy.export.verifySize", size);
      EasyDiagnostics.Print("easy.export.verifyNonEmpty", ok);
      return ok;
    }

    public static void ExportManifest(string path, IDictionary<string, string> values) {
      EasyEvidence.WriteManifest(path, values);
      EasyDiagnostics.Print("easy.export.manifestPath", path);
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
