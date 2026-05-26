using System;
using TFlex.Model;
using TFlexEasy;
using BOMObject = TFlex.Model.Model2D.BOMObject;

public class Program {
  public static int Main(){
    string source = Environment.GetEnvironmentVariable("TFLEX_PROTOTYPE_SOURCE_PATH");
    string fieldName = Environment.GetEnvironmentVariable("TFLEX_SPEC_STANDARD_FIELD");
    string expected = Environment.GetEnvironmentVariable("TFLEX_SPEC_FIELD_TEXT");
    bool addRecord = String.Equals(Environment.GetEnvironmentVariable("TFLEX_SPEC_ADD_RECORD"), "true", StringComparison.OrdinalIgnoreCase);
    if (String.IsNullOrWhiteSpace(source)) {
      EasyDiagnostics.Print("prototype.error", "TFLEX_PROTOTYPE_SOURCE_PATH is required");
      return 2;
    }
    if (expected == null) expected = "";

    Document doc = null;
    Document reopened = null;
    using (var sess = EasySession.Start3D()) {
      string copy = sess.ArtifactPath("spec_field_mutation_copy.grb");
      string output = sess.ArtifactPath("spec_field_mutation_saved.grb");
      try {
        BOMObject.StandardField field = EasySpecifications.ParseStandardField(fieldName);
        EasyPrototype.CopyToArtifact(source, copy);
        doc = EasyPrototype.OpenCopy(copy, visible: false);
        EasyDiagnostics.Print("spec.bom.exists", EasySpecifications.FirstBom(doc) != null);
        doc.BeginChanges("set prototype specification BOM field");
        bool set = EasySpecifications.SetFirstBomStandardFieldText(doc, field, expected, addRecord);
        var end = doc.EndChanges();
        EasyDiagnostics.Print("endChanges", end);
        EasyDiagnostics.Print("spec.field.set", set);
        bool saved = EasyPrototype.SaveAsGrb(doc, output);
        EasyPrototype.Close(doc);
        doc = null;

        reopened = EasyPrototype.OpenCopy(output, visible: false);
        string actual = EasySpecifications.FirstBomStandardFieldText(reopened, field);
        bool anyActual = EasySpecifications.AnyBomStandardFieldText(reopened, field, expected);
        EasyDiagnostics.Print("spec.field.reopened", actual);
        EasyDiagnostics.Print("spec.field.reopenedAny", anyActual);
        EasyDiagnostics.Print("spec.field.persisted", anyActual);
        return (saved && anyActual) ? 0 : 20;
      } finally {
        EasyPrototype.Close(reopened);
        EasyPrototype.Close(doc);
      }
    }
  }
}
