using System;
using System.Collections.Generic;
using System.IO;
using System.Text;
using TFlex.Model;
using TFlex.Model.Model3D;

namespace TFlexEasy {
  public static class EasyEvidence {
    public static void PrintOperationSummary(Document doc) {
      ICollection<Operation> operations = Document3D.GetOperations(doc);
      EasyDiagnostics.Print("evidence.operationCount", operations.Count);
      int index = 0;
      foreach (Operation op in operations) {
        string label = "evidence.operation." + index;
        EasyDiagnostics.Print(label + ".name", OperationName(op, "null"));
        EasyDiagnostics.Print(label + ".type", op == null ? "null" : op.GetType().FullName);
        if (op != null) EasyDiagnostics.PrintBodyBoxMm(label, op);
        index++;
      }
    }

    public static bool PrintFeatureCount(string key, int expected, int actual) {
      bool ok = expected == actual;
      EasyDiagnostics.Print(key + ".expected", expected);
      EasyDiagnostics.Print(key + ".actual", actual);
      EasyDiagnostics.Print(key + ".ok", ok);
      return ok;
    }

    public static bool AssertBbox(Operation op, double expectedX, double expectedY, double expectedZ, double toleranceMm) {
      BodyBoxMm box = EasyDiagnostics.PrintBodyBoxMm("evidence.assertBbox", op);
      bool ok = box.Valid
          && EasyDiagnostics.Near(box.SpanX, expectedX, toleranceMm)
          && EasyDiagnostics.Near(box.SpanY, expectedY, toleranceMm)
          && EasyDiagnostics.Near(box.SpanZ, expectedZ, toleranceMm);
      EasyDiagnostics.Print("evidence.assertBbox.expectedSpanMm", EasyUnits.F(expectedX) + "," + EasyUnits.F(expectedY) + "," + EasyUnits.F(expectedZ));
      EasyDiagnostics.Print("evidence.assertBbox.toleranceMm", EasyUnits.F(toleranceMm));
      EasyDiagnostics.Print("evidence.assertBbox.ok", ok);
      return ok;
    }

    public static bool AssertSaved(string path) {
      bool exists = File.Exists(path);
      long size = exists ? new FileInfo(path).Length : 0;
      bool ok = exists && size > 0;
      EasyDiagnostics.Print("evidence.saved.path", path);
      EasyDiagnostics.Print("evidence.saved.exists", exists);
      EasyDiagnostics.Print("evidence.saved.size", size);
      EasyDiagnostics.Print("evidence.saved.ok", ok);
      return ok;
    }

    public static int FailIfInvalidBbox(Operation op, int code) {
      BodyBoxMm box = EasyDiagnostics.GetBodyBoxMm(op);
      bool invalid = !box.Valid || box.SpanX <= 0 || box.SpanY <= 0 || box.SpanZ <= 0;
      EasyDiagnostics.Print("evidence.invalidBbox", invalid);
      return invalid ? code : 0;
    }

    public static void WriteManifest(string path, IDictionary<string, string> keyValues) {
      string dir = Path.GetDirectoryName(path);
      if (!String.IsNullOrWhiteSpace(dir)) Directory.CreateDirectory(dir);
      StringBuilder sb = new StringBuilder();
      sb.AppendLine("{");
      int index = 0;
      foreach (KeyValuePair<string, string> item in keyValues) {
        if (index > 0) sb.AppendLine(",");
        sb.Append("  \"").Append(JsonEscape(item.Key)).Append("\": \"").Append(JsonEscape(item.Value)).Append("\"");
        index++;
      }
      sb.AppendLine();
      sb.AppendLine("}");
      File.WriteAllText(path, sb.ToString());
      EasyDiagnostics.Print("evidence.manifestPath", path);
      EasyDiagnostics.Print("evidence.manifestExists", File.Exists(path));
    }

    static string JsonEscape(string value) {
      if (value == null) return "";
      return value.Replace("\\", "\\\\").Replace("\"", "\\\"");
    }

    static string OperationName(Operation op, string fallback) {
      if (op == null) return fallback;
      if (String.IsNullOrWhiteSpace(op.Name)) return op.GetType().Name;
      return op.Name;
    }
  }
}
