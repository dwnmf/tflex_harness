using System;
using System.IO;
using System.Text;
using TFlex.Model;
using TFlex.Model.Model3D;

namespace TFlexEasy {
  public static class EasyMateInspector {
    public static int PrintMates(Document doc) {
      int index = 0;
      foreach (Mate mate in Document3D.GetMates(doc)) {
        PrintMate(mate, "mateInspector.mate." + index);
        index++;
      }
      EasyDiagnostics.Print("mateInspector.mateCount", index);
      return index;
    }

    public static void PrintMateGeometryOwners(Document doc) {
      int index = 0;
      foreach (Mate mate in Document3D.GetMates(doc)) {
        EasyDiagnostics.Print("mateInspector.owner." + index + ".operation1", OperationName(SafeOperation1(mate)));
        EasyDiagnostics.Print("mateInspector.owner." + index + ".operation2", OperationName(SafeOperation2(mate)));
        EasyDiagnostics.Print("mateInspector.owner." + index + ".element1Type", mate.Element1 == null ? "null" : mate.Element1.GetType().FullName);
        EasyDiagnostics.Print("mateInspector.owner." + index + ".element2Type", mate.Element2 == null ? "null" : mate.Element2.GetType().FullName);
        index++;
      }
    }

    public static void WriteMateGraph(Document doc, string path) {
      string dir = Path.GetDirectoryName(path);
      if (!String.IsNullOrWhiteSpace(dir)) Directory.CreateDirectory(dir);
      StringBuilder sb = new StringBuilder();
      sb.AppendLine("{");
      sb.AppendLine("  \"mates\": [");
      int index = 0;
      foreach (Mate mate in Document3D.GetMates(doc)) {
        if (index > 0) sb.AppendLine(",");
        sb.Append("    {\"index\": ").Append(index)
          .Append(", \"type\": \"").Append(Escape(mate.Type.ToString())).Append("\"")
          .Append(", \"operation1\": \"").Append(Escape(OperationName(SafeOperation1(mate)))).Append("\"")
          .Append(", \"operation2\": \"").Append(Escape(OperationName(SafeOperation2(mate)))).Append("\"")
          .Append("}");
        index++;
      }
      sb.AppendLine();
      sb.AppendLine("  ]");
      sb.AppendLine("}");
      File.WriteAllText(path, sb.ToString());
      EasyDiagnostics.Print("mateInspector.graphPath", path);
      EasyDiagnostics.Print("mateInspector.graphExists", File.Exists(path));
    }

    public static string TryExplainMate(Mate mate) {
      if (mate == null) return "null_mate";
      string text = mate.Type + ":" + OperationName(SafeOperation1(mate)) + "->" + OperationName(SafeOperation2(mate));
      EasyDiagnostics.Print("mateInspector.explain", text);
      return text;
    }

    static void PrintMate(Mate mate, string label) {
      EasyDiagnostics.Print(label + ".name", String.IsNullOrWhiteSpace(mate.Name) ? "Mate" : mate.Name);
      EasyDiagnostics.Print(label + ".type", mate.Type);
      EasyDiagnostics.Print(label + ".operation1", OperationName(SafeOperation1(mate)));
      EasyDiagnostics.Print(label + ".operation2", OperationName(SafeOperation2(mate)));
      EasyDiagnostics.Print(label + ".element1Null", mate.Element1 == null);
      EasyDiagnostics.Print(label + ".element2Null", mate.Element2 == null);
      try { EasyDiagnostics.Print(label + ".suppressed", mate.Suppressed == null ? "null" : mate.Suppressed.ToString()); }
      catch (Exception ex) { EasyDiagnostics.Print(label + ".suppressedError", ex.GetType().Name + ": " + ex.Message); }
    }

    static Operation SafeOperation1(Mate mate) {
      try { return mate.Operation1; } catch { return null; }
    }

    static Operation SafeOperation2(Mate mate) {
      try { return mate.Operation2; } catch { return null; }
    }

    static string OperationName(Operation op) {
      if (op == null) return "null";
      return String.IsNullOrWhiteSpace(op.Name) ? op.GetType().Name : op.Name;
    }

    static string Escape(string value) {
      return (value ?? "").Replace("\\", "\\\\").Replace("\"", "\\\"");
    }
  }
}
