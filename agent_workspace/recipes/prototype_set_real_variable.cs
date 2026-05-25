using System;
using System.Globalization;
using TFlex.Model;
using TFlexEasy;

public class Program {
  public static int Main(){
    string source = Environment.GetEnvironmentVariable("TFLEX_PROTOTYPE_SOURCE_PATH");
    string variableName = Environment.GetEnvironmentVariable("TFLEX_VARIABLE_NAME");
    string expectedText = Environment.GetEnvironmentVariable("TFLEX_VARIABLE_REAL_VALUE");
    if (String.IsNullOrWhiteSpace(source)) {
      EasyDiagnostics.Print("prototype.error", "TFLEX_PROTOTYPE_SOURCE_PATH is required");
      return 2;
    }
    if (String.IsNullOrWhiteSpace(variableName)) {
      EasyDiagnostics.Print("variable.error", "TFLEX_VARIABLE_NAME is required");
      return 3;
    }
    double expected;
    if (!Double.TryParse(expectedText, NumberStyles.Float, CultureInfo.InvariantCulture, out expected)) {
      EasyDiagnostics.Print("variable.error", "TFLEX_VARIABLE_REAL_VALUE must be invariant-culture number");
      return 4;
    }

    Document doc = null;
    Document reopened = null;
    using (var sess = EasySession.Start3D()) {
      string copy = sess.ArtifactPath("real_variable_mutation_copy.grb");
      string output = sess.ArtifactPath("real_variable_mutation_saved.grb");
      try {
        EasyPrototype.CopyToArtifact(source, copy);
        doc = EasyPrototype.OpenCopy(copy, visible: false);
        EasyDiagnostics.Print("variable.name", variableName);
        EasyDiagnostics.Print("variable.exists", EasyVariables.Exists(doc, variableName));
        doc.BeginChanges("set prototype real variable");
        bool set = EasyVariables.SetRealConstant(doc, variableName, expected);
        var end = doc.EndChanges();
        EasyDiagnostics.Print("endChanges", end);
        EasyDiagnostics.Print("variable.set", set);
        bool saved = EasyPrototype.SaveAsGrb(doc, output);
        EasyPrototype.Close(doc);
        doc = null;

        reopened = EasyPrototype.OpenCopy(output, visible: false);
        double actual = EasyVariables.RealValue(reopened, variableName);
        EasyDiagnostics.Print("variable.reopened", actual);
        bool persisted = Math.Abs(actual - expected) < 1e-9;
        EasyDiagnostics.Print("variable.persisted", persisted);
        return (set && saved && persisted) ? 0 : 20;
      } finally {
        EasyPrototype.Close(reopened);
        EasyPrototype.Close(doc);
      }
    }
  }
}
