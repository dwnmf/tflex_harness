using System;
using TFlex.Model;
using TFlexEasy;

public class Program {
  public static int Main(){
    string source = Environment.GetEnvironmentVariable("TFLEX_PROTOTYPE_SOURCE_PATH");
    string variableName = Environment.GetEnvironmentVariable("TFLEX_VARIABLE_NAME");
    string expected = Environment.GetEnvironmentVariable("TFLEX_VARIABLE_TEXT_VALUE");
    if (String.IsNullOrWhiteSpace(source)) {
      EasyDiagnostics.Print("prototype.error", "TFLEX_PROTOTYPE_SOURCE_PATH is required");
      return 2;
    }
    if (String.IsNullOrWhiteSpace(variableName)) {
      EasyDiagnostics.Print("variable.error", "TFLEX_VARIABLE_NAME is required");
      return 3;
    }
    if (expected == null) expected = "";

    Document doc = null;
    Document reopened = null;
    using (var sess = EasySession.Start3D()) {
      string copy = sess.ArtifactPath("variable_mutation_copy.grb");
      string output = sess.ArtifactPath("variable_mutation_saved.grb");
      try {
        EasyPrototype.CopyToArtifact(source, copy);
        doc = EasyPrototype.OpenCopy(copy, visible: false);
        EasyDiagnostics.Print("variable.name", variableName);
        EasyDiagnostics.Print("variable.exists", EasyVariables.Exists(doc, variableName));
        doc.BeginChanges("set prototype text variable");
        bool set = EasyVariables.SetTextConstant(doc, variableName, expected);
        var end = doc.EndChanges();
        EasyDiagnostics.Print("endChanges", end);
        EasyDiagnostics.Print("variable.set", set);
        bool saved = EasyPrototype.SaveAsGrb(doc, output);
        EasyPrototype.Close(doc);
        doc = null;

        reopened = EasyPrototype.OpenCopy(output, visible: false);
        string actual = EasyVariables.TextValue(reopened, variableName);
        EasyDiagnostics.Print("variable.reopened", actual);
        EasyDiagnostics.Print("variable.persisted", actual == expected);
        return (set && saved && actual == expected) ? 0 : 20;
      } finally {
        EasyPrototype.Close(reopened);
        EasyPrototype.Close(doc);
      }
    }
  }
}
