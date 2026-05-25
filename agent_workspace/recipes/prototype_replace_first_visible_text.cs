using System;
using TFlex.Model;
using TFlexEasy;

public class Program {
  public static int Main() {
    string source = Environment.GetEnvironmentVariable("TFLEX_PROTOTYPE_SOURCE_PATH");
    string replacement = Environment.GetEnvironmentVariable("TFLEX_VISIBLE_TEXT_REPLACEMENT") ?? "";
    if (String.IsNullOrWhiteSpace(source)) {
      EasyDiagnostics.Print("firstVisibleText.error", "TFLEX_PROTOTYPE_SOURCE_PATH is required");
      return 2;
    }

    using (var sess = EasySession.Start3D()) {
      Document doc = null;
      Document reopened = null;
      try {
        string copy = sess.ArtifactPath("first_visible_text_replace_copy.grb");
        string output = sess.ArtifactPath("first_visible_text_replace_saved.grb");
        EasyPrototype.CopyToArtifact(source, copy);
        doc = EasyPrototype.OpenCopy(copy, visible: false);
        string before = EasyText.FirstVisibleText(doc) ?? "";
        EasyDiagnostics.Print("firstVisibleText.before", before);
        EasyDiagnostics.Print("firstVisibleText.replacement", replacement);
        doc.BeginChanges("replace first visible 2D text");
        bool set = EasyText.ReplaceFirstVisibleText(doc, replacement);
        var end = doc.EndChanges();
        EasyDiagnostics.Print("endChanges", end);
        EasyDiagnostics.Print("firstVisibleText.set", set);
        bool saved = EasyPrototype.SaveAsGrb(doc, output);
        EasyDiagnostics.Print("document.saved", saved);
        EasyDiagnostics.Print("document.outputPath", output);
        EasyDiagnostics.Print("document.outputExists", System.IO.File.Exists(output));
        if (System.IO.File.Exists(output)) EasyDiagnostics.Print("document.outputSize", new System.IO.FileInfo(output).Length);
        EasyPrototype.Close(doc);
        doc = null;
        reopened = EasyPrototype.OpenCopy(output, visible: false);
        string actual = EasyText.FirstVisibleText(reopened) ?? "";
        EasyDiagnostics.Print("firstVisibleText.reopened", actual);
        bool persisted = set && saved && actual == replacement;
        EasyDiagnostics.Print("firstVisibleText.persisted", persisted);
        EasyPrototype.Close(reopened);
        reopened = null;
        return persisted ? 0 : 20;
      } catch (Exception ex) {
        EasyDiagnostics.Print("exceptionType", ex.GetType().FullName);
        EasyDiagnostics.Print("exception", ex.Message);
        Console.WriteLine(ex.ToString());
        return 99;
      } finally {
        EasyPrototype.Close(reopened);
        EasyPrototype.Close(doc);
      }
    }
  }
}
