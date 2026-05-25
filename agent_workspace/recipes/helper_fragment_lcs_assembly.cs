using System;
using System.IO;
using TFlex.Model;
using TFlex.Model.Model3D;
using TFlexEasy;

public class Program {
  static PointsLCS MakeLcs(Document doc, string name, double ox, double oy, double oz) {
    CoordinateNode3D origin = new CoordinateNode3D(doc); origin.X = ox; origin.Y = oy; origin.Z = oz;
    CoordinateNode3D xpt = new CoordinateNode3D(doc); xpt.X = ox + 10; xpt.Y = oy; xpt.Z = oz;
    CoordinateNode3D ypt = new CoordinateNode3D(doc); ypt.X = ox; ypt.Y = oy + 10; ypt.Z = oz;
    PointsLCS lcs = new PointsLCS(doc);
    lcs.Name = name;
    lcs.UseForFragment = true;
    lcs.UseForFragmentFixing = true;
    lcs.PointToOrigin = origin.Geometry.Point;
    lcs.PointToAxisX = xpt.Geometry.Point;
    lcs.PointToAxisY = ypt.Geometry.Point;
    return lcs;
  }

  public static int Main() {
    using (var sess = EasySession.Start3D()) {
      Document part = null;
      Document asm = null;
      try {
        string partFile = sess.ArtifactPath("helper_fragment_lcs_part.grb");
        string asmFile = sess.ArtifactPath("helper_fragment_lcs_assembly.grb");

        part = sess.New3DDocument(false);
        part.BeginChanges("part with fragment LCS");
        Block block = new Block(part);
        block.Name = "part_block";
        block.Cube = false;
        block.Symmetry = true;
        block.XSize = 40;
        block.YSize = 20;
        block.ZSize = 10;
        PointsLCS source = MakeLcs(part, "FRAG_LCS", 0, 0, 0);
        var partEnd = part.EndChanges();
        EasyDiagnostics.Print("part.end", partEnd);
        EasyDiagnostics.Print("part.operations", Document3D.GetOperations(part).Count);
        EasyDiagnostics.Print("source.useForFragment", source.UseForFragment);
        EasyDiagnostics.Print("source.useForFragmentFixing", source.UseForFragmentFixing);
        bool partSaved = part.SaveAs(partFile);
        EasyDiagnostics.Print("part.saved", partSaved);
        EasyDiagnostics.Print("part.outputPath", partFile);
        EasyDiagnostics.Print("part.outputExists", File.Exists(partFile));
        if (File.Exists(partFile)) EasyDiagnostics.Print("part.outputSize", new FileInfo(partFile).Length);
        part.Close(); part = null;

        asm = sess.New3DDocument(false);
        int before = Document3D.GetOperations(asm).Count;
        asm.BeginChanges("assembly fragment by LCS");
        PointsLCS target = MakeLcs(asm, "ASM_TARGET_LCS", 100, 50, 20);
        Fragment3D fragment = new Fragment3D(partFile, asm);
        fragment.Name = "fragment_block";
        fragment.FixByFragmentLCS("FRAG_LCS", target);
        EasyDiagnostics.Print("fragment.sourceLcs", fragment.SourceLCSName);
        EasyDiagnostics.Print("fragment.targetLcsNull", fragment.TargetLCS == null);
        var asmEnd = asm.EndChanges();
        int after = Document3D.GetOperations(asm).Count;
        EasyDiagnostics.Print("assembly.end", asmEnd);
        EasyDiagnostics.Print("assembly.operationsBefore", before);
        EasyDiagnostics.Print("assembly.operationsAfter", after);
        EasyDiagnostics.Print("fragment.filePath", fragment.FilePath);
        EasyDiagnostics.Print("fragment.sourceLcsAfter", fragment.SourceLCSName);
        EasyDiagnostics.Print("fragment.targetLcsNullAfter", fragment.TargetLCS == null);
        bool asmSaved = asm.SaveAs(asmFile);
        EasyDiagnostics.Print("assembly.saved", asmSaved);
        EasyDiagnostics.Print("assembly.outputPath", asmFile);
        EasyDiagnostics.Print("assembly.outputExists", File.Exists(asmFile));
        if (File.Exists(asmFile)) EasyDiagnostics.Print("assembly.outputSize", new FileInfo(asmFile).Length);
        bool ok = partEnd.ToString() == "OK" && asmEnd.ToString() == "OK" && partSaved && asmSaved && after > before && fragment.SourceLCSName == "FRAG_LCS" && fragment.TargetLCS != null && File.Exists(partFile) && File.Exists(asmFile);
        EasyDiagnostics.Print("fragmentAssembly.persisted", ok);
        return ok ? 0 : 20;
      } catch (Exception ex) {
        EasyDiagnostics.Print("exceptionType", ex.GetType().FullName);
        EasyDiagnostics.Print("exception", ex.Message);
        Console.WriteLine(ex.ToString());
        return 99;
      } finally {
        try { if (asm != null) asm.Close(); } catch {}
        try { if (part != null) part.Close(); } catch {}
      }
    }
  }
}
