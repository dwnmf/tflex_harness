using System;
using System.IO;
using TFlex;
using TFlex.Model;
using TFlex.Model.Model3D;

namespace TFlexEasy {
  public sealed class EasyReopenResult {
    public string Path;
    public bool Saved;
    public bool Reopened;
    public int OperationCount;
    public BodyBoxMm BBox;
    public Document Document;
  }

  public static class EasyReopen {
    public static EasyReopenResult SaveCloseReopen3D(EasySession sess, Document doc, string path) {
      if (sess == null) throw new ArgumentNullException("sess");
      if (doc == null) throw new ArgumentNullException("doc");
      bool saved = EasyExport.Grb(doc, path);
      sess.Close(doc);
      Document reopened = Application.OpenDocument(path, false, false);
      EasyReopenResult result = BuildResult(path, saved, reopened);
      EasyDiagnostics.Print("reopen.saved", saved);
      EasyDiagnostics.Print("reopen.reopened", result.Reopened);
      EasyDiagnostics.Print("reopen.operationCount", result.OperationCount);
      if (reopened != null) EasyDiagnostics.PrintBodyBoxMm("reopen.firstOperation", FirstOperation(reopened));
      return result;
    }

    public static EasyReopenResult VerifyReopened(string path, int expectedMinOperations, BodyBoxMm expectedBbox) {
      Document reopened = Application.OpenDocument(path, false, false);
      EasyReopenResult result = BuildResult(path, File.Exists(path), reopened);
      bool countOk = result.OperationCount >= expectedMinOperations;
      bool bboxOk = !expectedBbox.Valid || (result.BBox.Valid
          && EasyDiagnostics.Near(result.BBox.SpanX, expectedBbox.SpanX, 0.5)
          && EasyDiagnostics.Near(result.BBox.SpanY, expectedBbox.SpanY, 0.5)
          && EasyDiagnostics.Near(result.BBox.SpanZ, expectedBbox.SpanZ, 0.5));
      EasyDiagnostics.Print("reopen.verify.path", path);
      EasyDiagnostics.Print("reopen.verify.expectedMinOperations", expectedMinOperations);
      EasyDiagnostics.Print("reopen.verify.operationCount", result.OperationCount);
      EasyDiagnostics.Print("reopen.verify.countOk", countOk);
      EasyDiagnostics.Print("reopen.verify.bboxOk", bboxOk);
      return result;
    }

    public static void PrintReopenEvidence(EasyReopenResult result, string label) {
      if (result == null) {
        EasyDiagnostics.Print(label + ".reopenResultNull", true);
        return;
      }
      EasyDiagnostics.Print(label + ".path", result.Path);
      EasyDiagnostics.Print(label + ".saved", result.Saved);
      EasyDiagnostics.Print(label + ".reopened", result.Reopened);
      EasyDiagnostics.Print(label + ".operationCount", result.OperationCount);
      EasyDiagnostics.Print(label + ".bboxValid", result.BBox.Valid);
      EasyDiagnostics.Print(label + ".bboxSpanMm", EasyUnits.F(result.BBox.SpanX) + "," + EasyUnits.F(result.BBox.SpanY) + "," + EasyUnits.F(result.BBox.SpanZ));
    }

    static EasyReopenResult BuildResult(string path, bool saved, Document doc) {
      Operation first = FirstOperation(doc);
      return new EasyReopenResult {
        Path = path,
        Saved = saved,
        Reopened = doc != null,
        OperationCount = doc == null ? 0 : Document3D.GetOperations(doc).Count,
        BBox = EasyDiagnostics.GetBodyBoxMm(first),
        Document = doc
      };
    }

    static Operation FirstOperation(Document doc) {
      if (doc == null) return null;
      foreach (Operation op in Document3D.GetOperations(doc)) return op;
      return null;
    }
  }
}
