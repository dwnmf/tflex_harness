using System;
using TFlex.Model;
using TFlex.Model.Model2D;
using BOMObject = TFlex.Model.Model2D.BOMObject;

namespace TFlexEasy {
  public static class EasySpecifications {
    public static BOMObject FirstBom(Document doc) {
      if (doc == null) throw new ArgumentNullException("doc");
      foreach (Object2D obj in doc.Get2DObjects()) {
        BOMObject bom = obj as BOMObject;
        if (bom != null) return bom;
      }
      return null;
    }

    public static BOMObject.StandardField ParseStandardField(string fieldName) {
      if (String.IsNullOrWhiteSpace(fieldName)) return BOMObject.StandardField.Desc;
      return (BOMObject.StandardField)Enum.Parse(typeof(BOMObject.StandardField), fieldName, true);
    }

    public static string FirstBomStandardFieldText(Document doc, BOMObject.StandardField field) {
      BOMObject bom = FirstBom(doc);
      if (bom == null) return null;
      bool editing = false;
      try {
        bom.BeginEdit();
        editing = true;
        bom.MoveToFrontRecord();
        return bom.GetStandardFieldValue(field);
      } catch (Exception ex) {
        EasyDiagnostics.Print("spec.read.error", ex.GetType().Name + ": " + ex.Message);
        return null;
      } finally {
        if (editing) bom.EndEdit();
      }
    }

    public static bool AnyBomStandardFieldText(Document doc, BOMObject.StandardField field, string expected) {
      return AnyBomStandardFieldText(doc, field, expected, 256);
    }

    public static bool AnyBomStandardFieldText(Document doc, BOMObject.StandardField field, string expected, int maxRecords) {
      if (expected == null) expected = "";
      BOMObject bom = FirstBom(doc);
      if (bom == null) return false;
      bool editing = false;
      try {
        bom.BeginEdit();
        editing = true;
        bom.MoveToFrontRecord();
        uint previousId = UInt32.MaxValue;
        for (int index = 0; index < maxRecords; index++) {
          uint id = bom.RecordID;
          string text = bom.GetStandardFieldValue(field);
          EasyDiagnostics.Print("spec.scan." + index + ".recordID", id);
          EasyDiagnostics.Print("spec.scan." + index + ".field", text);
          if (text == expected) return true;
          bom.MoveToNextRecord();
          uint nextId = bom.RecordID;
          if (nextId == id || nextId == previousId) break;
          previousId = id;
        }
        return false;
      } catch (Exception ex) {
        EasyDiagnostics.Print("spec.scan.error", ex.GetType().Name + ": " + ex.Message);
        return false;
      } finally {
        if (editing) bom.EndEdit();
      }
    }

    public static bool SetFirstBomStandardFieldText(Document doc, BOMObject.StandardField field, string value) {
      return SetFirstBomStandardFieldText(doc, field, value, false);
    }

    public static bool SetFirstBomStandardFieldText(Document doc, BOMObject.StandardField field, string value, bool addRecord) {
      if (value == null) value = "";
      BOMObject bom = FirstBom(doc);
      if (bom == null) {
        EasyDiagnostics.Print("spec.error", "BOMObject not found");
        return false;
      }
      bool editing = false;
      try {
        bom.BeginEdit();
        editing = true;
        bom.MoveToFrontRecord();
        string before = bom.GetStandardFieldValue(field);
        if (addRecord) {
          bom.AddRecord();
          EasyDiagnostics.Print("spec.record.added", true);
        }
        EasyDiagnostics.Print("spec.field", field.ToString());
        EasyDiagnostics.Print("spec.field.before", before);
        bom.UpdateStandardFieldValue(field, value);
        bom.UpdateRecord();
        string after = bom.GetStandardFieldValue(field);
        EasyDiagnostics.Print("spec.field.after", after);
        return after == value;
      } catch (Exception ex) {
        EasyDiagnostics.Print("spec.error", ex.GetType().Name + ": " + ex.Message);
        return false;
      } finally {
        if (editing) bom.EndEdit();
      }
    }
  }
}
