using System;
using TFlex.Model;
using TFlexEasy;

public class Program {
  public static int Main(){
    string source = Environment.GetEnvironmentVariable("TFLEX_PROTOTYPE_SOURCE_PATH");
    if (String.IsNullOrWhiteSpace(source)) {
      EasyDiagnostics.Print("prototype.error", "TFLEX_PROTOTYPE_SOURCE_PATH is required");
      return 2;
    }

    Document doc = null;
    using (var sess = EasySession.Start3D()) {
      string copy = sess.ArtifactPath("prototype_copy.grb");
      string output = sess.ArtifactPath("prototype_saved.grb");
      try {
        EasyPrototype.CopyToArtifact(source, copy);
        doc = EasyPrototype.OpenCopy(copy, visible: false);
        bool saved = EasyPrototype.SaveAsGrb(doc, output);
        EasyPrototype.PrintPrototypeEvidence("prototype", source, copy, output);
        return saved ? 0 : 20;
      } finally {
        EasyPrototype.Close(doc);
      }
    }
  }
}
