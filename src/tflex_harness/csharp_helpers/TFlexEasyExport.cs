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
  }
}
