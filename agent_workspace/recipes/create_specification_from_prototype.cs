using System;
using TFlex.Model;
using TFlexEasy;

public class Program {
  public static int Main(){
    string source = Environment.GetEnvironmentVariable("TFLEX_PROTOTYPE_SOURCE_PATH");
    string propertyName = Environment.GetEnvironmentVariable("TFLEX_DOCUMENT_PROPERTY_NAME");
    string expected = Environment.GetEnvironmentVariable("TFLEX_DOCUMENT_PROPERTY_TEXT");
    if (String.IsNullOrWhiteSpace(source)) {
      EasyDiagnostics.Print("prototype.error", "TFLEX_PROTOTYPE_SOURCE_PATH is required");
      return 2;
    }
    if (String.IsNullOrWhiteSpace(propertyName)) {
      EasyDiagnostics.Print("documentProperty.error", "TFLEX_DOCUMENT_PROPERTY_NAME is required");
      return 3;
    }
    if (expected == null) expected = "";

    Document doc = null;
    Document reopened = null;
    using (var sess = EasySession.Start3D()) {
      string copy = sess.ArtifactPath("document_property_mutation_copy.grb");
      string output = sess.ArtifactPath("document_property_mutation_saved.grb");
      try {
        EasyPrototype.CopyToArtifact(source, copy);
        doc = EasyPrototype.OpenCopy(copy, visible: false);
        EasyDiagnostics.Print("documentProperty.name", propertyName);
        EasyDiagnostics.Print("documentProperty.exists", EasyDocumentProperties.FindStringProperty(doc, propertyName) != null);
        doc.BeginChanges("set prototype document property");
        bool set = EasyDocumentProperties.SetText(doc, propertyName, expected);
        var end = doc.EndChanges();
        EasyDiagnostics.Print("endChanges", end);
        EasyDiagnostics.Print("documentProperty.set", set);
        bool saved = EasyPrototype.SaveAsGrb(doc, output);
        EasyPrototype.Close(doc);
        doc = null;

        reopened = EasyPrototype.OpenCopy(output, visible: false);
        string actual = EasyDocumentProperties.Text(reopened, propertyName);
        EasyDiagnostics.Print("documentProperty.reopened", actual);
        EasyDiagnostics.Print("documentProperty.persisted", actual == expected);
        return (set && saved && actual == expected) ? 0 : 20;
      } finally {
        EasyPrototype.Close(reopened);
        EasyPrototype.Close(doc);
      }
    }
  }
}
