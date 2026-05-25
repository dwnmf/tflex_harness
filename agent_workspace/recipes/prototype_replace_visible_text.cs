using System;
using TFlex.Model;
using TFlexEasy;

public class Program {
  public static int Main(){
    string source = Environment.GetEnvironmentVariable("TFLEX_PROTOTYPE_SOURCE_PATH");
    string search = Environment.GetEnvironmentVariable("TFLEX_VISIBLE_TEXT_SEARCH");
    string replacement = Environment.GetEnvironmentVariable("TFLEX_VISIBLE_TEXT_REPLACEMENT");
    if (String.IsNullOrWhiteSpace(source)) {
      EasyDiagnostics.Print("prototype.error", "TFLEX_PROTOTYPE_SOURCE_PATH is required");
      return 2;
    }
    if (String.IsNullOrEmpty(search)) {
      EasyDiagnostics.Print("visibleText.error", "TFLEX_VISIBLE_TEXT_SEARCH is required");
      return 3;
    }
    if (replacement == null) replacement = "";

    Document doc = null;
    Document reopened = null;
    using (var sess = EasySession.Start3D()) {
      string copy = sess.ArtifactPath("visible_text_replace_copy.grb");
      string output = sess.ArtifactPath("visible_text_replace_saved.grb");
      try {
        EasyPrototype.CopyToArtifact(source, copy);
        doc = EasyPrototype.OpenCopy(copy, visible: false);
        int before = EasyText.CountVisibleTextOccurrences(doc, search);
        EasyDiagnostics.Print("visibleText.search", search);
        EasyDiagnostics.Print("visibleText.replacement", replacement);
        EasyDiagnostics.Print("visibleText.beforeCount", before);
        doc.BeginChanges("replace visible 2D text");
        int replaced = EasyText.ReplaceVisibleText(doc, search, replacement);
        var end = doc.EndChanges();
        EasyDiagnostics.Print("endChanges", end);
        EasyDiagnostics.Print("visibleText.replaceCount", replaced);
        bool saved = EasyPrototype.SaveAsGrb(doc, output);
        EasyPrototype.Close(doc);
        doc = null;

        reopened = EasyPrototype.OpenCopy(output, visible: false);
        int oldAfter = EasyText.CountVisibleTextOccurrences(reopened, search);
        int newAfter = EasyText.CountVisibleTextOccurrences(reopened, replacement);
        EasyDiagnostics.Print("visibleText.oldAfter", oldAfter);
        EasyDiagnostics.Print("visibleText.newAfter", newAfter);
        bool persisted = before > 0 && replaced == before && oldAfter == 0 && newAfter >= replaced;
        EasyDiagnostics.Print("visibleText.persisted", persisted);
        return (saved && persisted) ? 0 : 20;
      } finally {
        EasyPrototype.Close(reopened);
        EasyPrototype.Close(doc);
      }
    }
  }
}
