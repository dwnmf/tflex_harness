using System.Collections.Generic;
using System.IO;
using TFlexEasy;

public class Program {
  public static int Main(){
    string dir = System.Environment.GetEnvironmentVariable("TFLEX_HARNESS_ARTIFACTS_DIR");
    if (System.String.IsNullOrWhiteSpace(dir)) dir = Directory.GetCurrentDirectory();
    Directory.CreateDirectory(dir);
    string savedPath = Path.Combine(dir, "evidence_saved.txt");
    File.WriteAllText(savedPath, "non-empty");
    bool countOk = EasyEvidence.PrintFeatureCount("evidenceUnit.featureCount", 3, 3);
    bool countFail = EasyEvidence.PrintFeatureCount("evidenceUnit.featureCountMismatch", 3, 2);
    bool savedOk = EasyEvidence.AssertSaved(savedPath);
    bool missingOk = !EasyEvidence.AssertSaved(Path.Combine(dir, "missing.txt"));
    int invalidCode = EasyEvidence.FailIfInvalidBbox(null, 77);
    string manifestPath = Path.Combine(dir, "evidence_unit_manifest.json");
    EasyEvidence.WriteManifest(manifestPath, new Dictionary<string,string> {
      {"quote", "a\"b"},
      {"slash", "a\\b"},
      {"countOk", countOk.ToString()}
    });
    string manifest = File.ReadAllText(manifestPath);
    bool manifestOk = File.Exists(manifestPath) && manifest.Contains("\\\"") && manifest.Contains("\\\\") && manifest.Contains("countOk");
    bool failIfOk = invalidCode == 77;
    EasyDiagnostics.Print("evidenceUnit.countOk", countOk);
    EasyDiagnostics.Print("evidenceUnit.countFailDetected", !countFail);
    EasyDiagnostics.Print("evidenceUnit.savedOk", savedOk);
    EasyDiagnostics.Print("evidenceUnit.missingDetected", missingOk);
    EasyDiagnostics.Print("evidenceUnit.failIfInvalidBboxCode", invalidCode);
    EasyDiagnostics.Print("evidenceUnit.manifestOk", manifestOk);
    bool ok = countOk && !countFail && savedOk && missingOk && failIfOk && manifestOk;
    EasyDiagnostics.Print("evidenceUnit.expectedClean", ok);
    return ok ? 0 : 10;
  }
}
