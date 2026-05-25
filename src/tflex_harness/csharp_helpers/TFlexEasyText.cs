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
      } catch (Exception ex) {
        EasyDiagnostics.Print("table.read.error", ex.GetType().Name + ": " + ex.Message);
        return null;
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

    public static int CountVisibleTextOccurrences(Document doc, string search) {
      if (doc == null) throw new ArgumentNullException("doc");
      if (String.IsNullOrEmpty(search)) return 0;
      int count = 0;
      foreach (Object2D obj in doc.Get2DObjects()) {
        LineText line = obj as LineText;
        if (line != null) {
          count += CountOccurrences(line.TextValue, search);
          continue;
        }
        RichText rich = obj as RichText;
        if (rich != null) {
          bool editing = false;
          try {
            rich.BeginEdit();
            editing = true;
            if (!rich.TableOnly) count += CountOccurrences(rich.TextValue, search);
          } catch {
          } finally {
            if (editing) rich.EndEdit();
          }
        }
      }
      return count;
    }

    public static int ReplaceVisibleText(Document doc, string search, string replacement) {
      if (doc == null) throw new ArgumentNullException("doc");
      if (String.IsNullOrEmpty(search)) return 0;
      if (replacement == null) replacement = "";
      int replaced = 0;
      foreach (Object2D obj in doc.Get2DObjects()) {
        LineText line = obj as LineText;
        if (line != null) {
          string before = line.TextValue;
          int hits = CountOccurrences(before, search);
          if (hits > 0) {
            EasyDiagnostics.Print("visibleText.line.before", before);
            line.TextValue = before.Replace(search, replacement);
            EasyDiagnostics.Print("visibleText.line.after", line.TextValue);
            replaced += hits;
          }
          continue;
        }
        RichText rich = obj as RichText;
        if (rich != null) {
          bool editing = false;
          try {
            rich.BeginEdit();
            editing = true;
            if (!rich.TableOnly) {
              string before = rich.TextValue;
              int hits = CountOccurrences(before, search);
              if (hits > 0) {
                EasyDiagnostics.Print("visibleText.rich.before", before);
                rich.ClearAll();
                rich.InsertText(before.Replace(search, replacement));
                EasyDiagnostics.Print("visibleText.rich.after", rich.TextValue);
                replaced += hits;
              }
            }
          } catch (Exception ex) {
            EasyDiagnostics.Print("visibleText.rich.error", ex.GetType().Name + ": " + ex.Message);
          } finally {
            if (editing) rich.EndEdit();
          }
        }
      }
      EasyDiagnostics.Print("visibleText.replaced", replaced);
      return replaced;
    }

    public static string FirstVisibleText(Document doc) {
      if (doc == null) throw new ArgumentNullException("doc");
      foreach (Object2D obj in doc.Get2DObjects()) {
        LineText line = obj as LineText;
        if (line != null && !String.IsNullOrWhiteSpace(line.TextValue)) return line.TextValue;
        RichText rich = obj as RichText;
        if (rich != null) {
          bool editing = false;
          try {
            rich.BeginEdit();
            editing = true;
            if (!rich.TableOnly && !String.IsNullOrWhiteSpace(rich.TextValue)) return rich.TextValue;
          } catch {
          } finally {
            if (editing) rich.EndEdit();
          }
        }
      }
      return null;
    }

    public static bool ReplaceFirstVisibleText(Document doc, string replacement) {
      if (doc == null) throw new ArgumentNullException("doc");
      if (replacement == null) replacement = "";
      foreach (Object2D obj in doc.Get2DObjects()) {
        LineText line = obj as LineText;
        if (line != null && !String.IsNullOrWhiteSpace(line.TextValue)) {
          EasyDiagnostics.Print("firstVisibleText.kind", "LineText");
          EasyDiagnostics.Print("firstVisibleText.before", line.TextValue);
          line.TextValue = replacement;
          EasyDiagnostics.Print("firstVisibleText.after", line.TextValue);
          return line.TextValue == replacement;
        }
        RichText rich = obj as RichText;
        if (rich != null) {
          bool editing = false;
          try {
            rich.BeginEdit();
            editing = true;
            if (!rich.TableOnly && !String.IsNullOrWhiteSpace(rich.TextValue)) {
              EasyDiagnostics.Print("firstVisibleText.kind", "RichText");
              EasyDiagnostics.Print("firstVisibleText.before", rich.TextValue);
              rich.ClearAll();
              rich.InsertText(replacement);
              EasyDiagnostics.Print("firstVisibleText.after", rich.TextValue);
              return rich.TextValue == replacement;
            }
          } catch (Exception ex) {
            EasyDiagnostics.Print("firstVisibleText.rich.error", ex.GetType().Name + ": " + ex.Message);
          } finally {
            if (editing) rich.EndEdit();
          }
        }
      }
      EasyDiagnostics.Print("firstVisibleText.error", "visible text not found");
      return false;
    }

    static int CountOccurrences(string value, string search) {
      if (String.IsNullOrEmpty(value) || String.IsNullOrEmpty(search)) return 0;
      int count = 0;
      int index = 0;
      while (true) {
        index = value.IndexOf(search, index, StringComparison.Ordinal);
        if (index < 0) break;
        count++;
        index += search.Length;
      }
      return count;
    }
  }
}
