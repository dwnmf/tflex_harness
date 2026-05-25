using System;
using TFlex.Model;
using TFlexEasy;

public class Program {
  public static int Main(){
    string source = Environment.GetEnvironmentVariable("TFLEX_PROTOTYPE_SOURCE_PATH");
    string cellText = Environment.GetEnvironmentVariable("TFLEX_TABLE_CELL_INDEX");
    string expected = Environment.GetEnvironmentVariable("TFLEX_TABLE_CELL_TEXT");
    if (String.IsNullOrWhiteSpace(source)) {
      EasyDiagnostics.Print("prototype.error", "TFLEX_PROTOTYPE_SOURCE_PATH is required");
      return 2;
    }
    uint cell;
    if (!UInt32.TryParse(cellText, out cell)) {
      EasyDiagnostics.Print("table.error", "TFLEX_TABLE_CELL_INDEX must be uint");
      return 3;
    }
    if (expected == null) expected = "";

    Document doc = null;
    Document reopened = null;
    using (var sess = EasySession.Start3D()) {
      string copy = sess.ArtifactPath("table_cell_mutation_copy.grb");
      string output = sess.ArtifactPath("table_cell_mutation_saved.grb");
      try {
        EasyPrototype.CopyToArtifact(source, copy);
        doc = EasyPrototype.OpenCopy(copy, visible: false);
        EasyDiagnostics.Print("richText.count", EasyText.CountRichTexts(doc));
        EasyDiagnostics.Print("table.cell.index", cell);
        doc.BeginChanges("set prototype table cell");
        bool set = EasyText.SetFirstTableCellText(doc, cell, expected);
        var end = doc.EndChanges();
        EasyDiagnostics.Print("endChanges", end);
        EasyDiagnostics.Print("table.cell.set", set);
        bool saved = EasyPrototype.SaveAsGrb(doc, output);
        EasyPrototype.Close(doc);
        doc = null;

        reopened = EasyPrototype.OpenCopy(output, visible: false);
        string actual = EasyText.FirstTableCellText(reopened, cell);
        EasyDiagnostics.Print("table.cell.reopened", actual);
        EasyDiagnostics.Print("table.cell.persisted", actual == expected);
        return (set && saved && actual == expected) ? 0 : 20;
      } finally {
        EasyPrototype.Close(reopened);
        EasyPrototype.Close(doc);
      }
    }
  }
}
