using System;
using System.IO;
using System.Security.Cryptography;
using TFlex;
using TFlex.Model;

namespace TFlexEasy {
  public static class EasyPrototype {
    public static string CopyToArtifact(string sourcePath, string artifactPath) {
      if (String.IsNullOrWhiteSpace(sourcePath)) throw new ArgumentException("sourcePath is required", "sourcePath");
      if (String.IsNullOrWhiteSpace(artifactPath)) throw new ArgumentException("artifactPath is required", "artifactPath");
      if (!File.Exists(sourcePath)) throw new FileNotFoundException("Prototype source file not found", sourcePath);

      string dir = Path.GetDirectoryName(artifactPath);
      if (!String.IsNullOrWhiteSpace(dir)) Directory.CreateDirectory(dir);
      File.Copy(sourcePath, artifactPath, true);
      EasyDiagnostics.Print("prototype.sourcePath", sourcePath);
      EasyDiagnostics.Print("prototype.sourceSize", new FileInfo(sourcePath).Length);
      EasyDiagnostics.Print("prototype.sourceSha256", Sha256(sourcePath));
      EasyDiagnostics.Print("prototype.copyPath", artifactPath);
      EasyDiagnostics.Print("prototype.copyExists", File.Exists(artifactPath));
      EasyDiagnostics.Print("prototype.copySize", new FileInfo(artifactPath).Length);
      EasyDiagnostics.Print("prototype.copySha256", Sha256(artifactPath));
      return artifactPath;
    }

    public static Document OpenCopy(string copiedPath, bool visible) {
      if (String.IsNullOrWhiteSpace(copiedPath)) throw new ArgumentException("copiedPath is required", "copiedPath");
      if (!File.Exists(copiedPath)) throw new FileNotFoundException("Prototype copy file not found", copiedPath);
      Document doc = Application.OpenDocument(copiedPath, visible, false);
      EasyDiagnostics.Print("document.opened", doc != null);
      EasyDiagnostics.Print("document.copyPath", copiedPath);
      if (doc == null) throw new InvalidOperationException("Application.OpenDocument returned null for " + copiedPath);
      return doc;
    }

    public static bool SaveAsGrb(Document doc, string outputPath) {
      if (doc == null) throw new ArgumentNullException("doc");
      if (String.IsNullOrWhiteSpace(outputPath)) throw new ArgumentException("outputPath is required", "outputPath");
      string dir = Path.GetDirectoryName(outputPath);
      if (!String.IsNullOrWhiteSpace(dir)) Directory.CreateDirectory(dir);
      bool saved = doc.SaveAs(outputPath);
      bool exists = File.Exists(outputPath);
      long size = exists ? new FileInfo(outputPath).Length : 0;
      EasyDiagnostics.Print("document.saved", saved);
      EasyDiagnostics.Print("document.outputPath", outputPath);
      EasyDiagnostics.Print("document.outputExists", exists);
      EasyDiagnostics.Print("document.outputSize", size);
      if (exists) EasyDiagnostics.Print("document.outputSha256", Sha256(outputPath));
      return saved && exists && size > 0;
    }

    public static void Close(Document doc) {
      if (doc == null) return;
      doc.Close();
      EasyDiagnostics.Print("document.closed", true);
    }

    public static void PrintPrototypeEvidence(string label, string sourcePath, string copiedPath, string outputPath) {
      EasyDiagnostics.Print(label + ".sourcePath", sourcePath);
      EasyDiagnostics.Print(label + ".sourceExists", File.Exists(sourcePath));
      if (File.Exists(sourcePath)) {
        EasyDiagnostics.Print(label + ".sourceSize", new FileInfo(sourcePath).Length);
        EasyDiagnostics.Print(label + ".sourceSha256", Sha256(sourcePath));
      }
      EasyDiagnostics.Print(label + ".copyPath", copiedPath);
      EasyDiagnostics.Print(label + ".copyExists", File.Exists(copiedPath));
      if (File.Exists(copiedPath)) EasyDiagnostics.Print(label + ".copySize", new FileInfo(copiedPath).Length);
      EasyDiagnostics.Print(label + ".outputPath", outputPath);
      EasyDiagnostics.Print(label + ".outputExists", File.Exists(outputPath));
      if (File.Exists(outputPath)) EasyDiagnostics.Print(label + ".outputSize", new FileInfo(outputPath).Length);
    }

    public static string Sha256(string path) {
      using (var sha = SHA256.Create()) {
        using (var stream = File.OpenRead(path)) {
          byte[] hash = sha.ComputeHash(stream);
          return BitConverter.ToString(hash).Replace("-", "").ToLowerInvariant();
        }
      }
    }
  }
}
