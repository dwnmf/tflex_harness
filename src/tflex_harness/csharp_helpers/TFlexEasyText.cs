using System;
using TFlex.Model;
using TFlex.Model.Model2D;

namespace TFlexEasy {
  public static class EasyText {
    public static int CountRichTexts(Document doc) {
      if (doc == null) throw new ArgumentNullException("doc");
      int count = 0;
      foreach (Object2D obj in doc.Get2DObjects()) {
        if (obj is RichText) count++;
      }
      return count;
    }

    public static RichText FirstRichText(Document doc) {
      if (doc == null) throw new ArgumentNullException("doc");
      foreach (Object2D obj in doc.Get2DObjects()) {
        if (obj is RichText) return (RichText)obj;
      }
      return null;
    }

    public static string FirstTableCellText(Document doc, uint cell) {
      RichText rich = FirstRichText(doc);
      if (rich == null) return null;
      bool editing = false;
      try {
        rich.BeginEdit();
        editing = true;
        Table table = rich.GetTableByIndex(0);
        return NormalizeCellText(table.GetCellText(cell));
      } finally {
        if (editing) rich.EndEdit();
      }
    }

    public static bool SetFirstTableCellText(Document doc, uint cell, string value) {
      if (value == null) value = "";
      RichText rich = FirstRichText(doc);
      if (rich == null) {
        EasyDiagnostics.Print("table.error", "RichText not found");
        return false;
      }
      bool editing = false;
      try {
        rich.BeginEdit();
        editing = true;
        Table table = rich.GetTableByIndex(0);
        string before = NormalizeCellText(table.GetCellText(cell));
        EasyDiagnostics.Print("table.cell.before", before);
        table.Clear(cell);
        table.InsertText(cell, 0, value);
        string after = NormalizeCellText(table.GetCellText(cell));
        EasyDiagnostics.Print("table.cell.after", after);
        return after == value;
      } catch (Exception ex) {
        EasyDiagnostics.Print("table.error", ex.GetType().Name + ": " + ex.Message);
        return false;
      } finally {
        if (editing) rich.EndEdit();
      }
    }

    public static string NormalizeCellText(string value) {
      if (value == null) return "";
      return value.Replace("\r\n", "\n").TrimEnd('\r', '\n');
    }
  }
}
