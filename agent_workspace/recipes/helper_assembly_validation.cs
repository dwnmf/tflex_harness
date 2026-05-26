using System;
using System.IO;
using TFlex.Model;
using TFlex.Model.Model3D;
using TFlexEasy;

public class Program {
  static PointsLCS MakeLcs(Document doc, string name, double ox, double oy, double oz) {
    ox = EasyUnits.MmToModel(ox);
    oy = EasyUnits.MmToModel(oy);
    oz = EasyUnits.MmToModel(oz);
    double axisLen = EasyUnits.MmToModel(10);
    CoordinateNode3D origin = new CoordinateNode3D(doc); origin.X = ox; origin.Y = oy; origin.Z = oz;
    CoordinateNode3D xpt = new CoordinateNode3D(doc); xpt.X = ox + axisLen; xpt.Y = oy; xpt.Z = oz;
    CoordinateNode3D ypt = new CoordinateNode3D(doc); ypt.X = ox; ypt.Y = oy + axisLen; ypt.Z = oz;
    PointsLCS lcs = new PointsLCS(doc);
    lcs.Name = name;
    lcs.UseForFragment = true;
    lcs.UseForFragmentFixing = true;
    lcs.PointToOrigin = origin.Geometry.Point;
    lcs.PointToAxisX = xpt.Geometry.Point;
    lcs.PointToAxisY = ypt.Geometry.Point;
    return lcs;
  }

  static string MakeSourcePart(EasySession sess) {
    Document part = null;
    try {
      string partFile = sess.ArtifactPath("assembly_validation_source_part.grb");
      part = sess.New3DDocument(false);
      part.BeginChanges("assembly validation source part");
      Block block = new Block(part);
      block.Name = "source_block_20";
      block.Cube = false;
      block.Symmetry = true;
      block.XSize = 20;
      block.YSize = 20;
      block.ZSize = 20;
      PointsLCS source = MakeLcs(part, "FRAG_LCS", 0, 0, 0);
      var end = part.EndChanges();
      EasyDiagnostics.Print("sourcePart.end", end);
      EasyDiagnostics.Print("sourcePart.operations", Document3D.GetOperations(part).Count);
      EasyDiagnostics.Print("sourcePart.lcs", source.Name);
      bool saved = part.SaveAs(partFile);
      EasyDiagnostics.Print("sourcePart.saved", saved);
      EasyDiagnostics.Print("sourcePart.path", partFile);
      EasyDiagnostics.Print("sourcePart.exists", File.Exists(partFile));
      if (File.Exists(partFile)) EasyDiagnostics.Print("sourcePart.size", new FileInfo(partFile).Length);
      return partFile;
    } finally {
      if (part != null) sess.Close(part);
    }
  }

  static string MakeBadAssembly(EasySession sess, string partFile) {
    Document asm = null;
    try {
      string asmFile = sess.ArtifactPath("assembly_validation_bad.grb");
      asm = sess.New3DDocument(false);
      asm.BeginChanges("bad assembly with overlap and floating fragment");
      PointsLCS root = MakeLcs(asm, "ROOT_LCS", 0, 0, 0);
      Fragment3D fixedFrag = new Fragment3D(partFile, asm);
      fixedFrag.Name = "fixed_overlap_fragment";
      fixedFrag.FixByFragmentLCS("FRAG_LCS", root);
      Fragment3D floating = new Fragment3D(partFile, asm);
      floating.Name = "floating_overlap_fragment";
      EasyDiagnostics.Print("bad.fixed.sourceLcs", fixedFrag.SourceLCSName);
      EasyDiagnostics.Print("bad.fixed.targetLcsNull", fixedFrag.TargetLCS == null);
      EasyDiagnostics.Print("bad.floating.fixing", floating.Fixing);
      EasyDiagnostics.Print("bad.floating.targetLcsNull", floating.TargetLCS == null);
      var end = asm.EndChanges();
      EasyDiagnostics.Print("bad.end", end);
      AssemblyValidationReport report = EasyAssemblyValidation.Validate(asm, "bad");
      bool saved = asm.SaveAs(asmFile);
      EasyDiagnostics.Print("bad.saved", saved);
      EasyDiagnostics.Print("bad.path", asmFile);
      EasyDiagnostics.Print("bad.exists", File.Exists(asmFile));
      if (File.Exists(asmFile)) EasyDiagnostics.Print("bad.size", new FileInfo(asmFile).Length);
      bool expected = report.CollisionCount > 0
        && report.FloatingFragmentCount > 0
        && report.GroundedFragmentCount == 1
        && report.UngroundedFragmentCount == 1
        && report.FullyConstrainedFragmentCount == 1
        && report.UnderConstrainedFragmentCount == 1
        && report.EstimatedDofRemaining == 6;
      EasyDiagnostics.Print("bad.expectedDetected", expected);
      return expected ? asmFile : "";
    } finally {
      if (asm != null) sess.Close(asm);
    }
  }

  static string MakeGoodAssembly(EasySession sess, string partFile) {
    Document asm = null;
    try {
      string asmFile = sess.ArtifactPath("assembly_validation_good.grb");
      asm = sess.New3DDocument(false);
      asm.BeginChanges("good assembly with fixed separated fragments");
      PointsLCS a = MakeLcs(asm, "ROOT_A", 0, 0, 0);
      PointsLCS b = MakeLcs(asm, "ROOT_B", 60, 0, 0);
      Fragment3D fragA = new Fragment3D(partFile, asm);
      fragA.Name = "fixed_fragment_a";
      fragA.FixByFragmentLCS("FRAG_LCS", a);
      Fragment3D fragB = new Fragment3D(partFile, asm);
      fragB.Name = "fixed_fragment_b";
      fragB.FixByFragmentLCS("FRAG_LCS", b);
      EasyDiagnostics.Print("good.a.sourceLcs", fragA.SourceLCSName);
      EasyDiagnostics.Print("good.a.targetLcsNull", fragA.TargetLCS == null);
      EasyDiagnostics.Print("good.b.sourceLcs", fragB.SourceLCSName);
      EasyDiagnostics.Print("good.b.targetLcsNull", fragB.TargetLCS == null);
      var end = asm.EndChanges();
      EasyDiagnostics.Print("good.end", end);
      AssemblyValidationReport report = EasyAssemblyValidation.Validate(asm, "good");
      bool saved = asm.SaveAs(asmFile);
      EasyDiagnostics.Print("good.saved", saved);
      EasyDiagnostics.Print("good.path", asmFile);
      EasyDiagnostics.Print("good.exists", File.Exists(asmFile));
      if (File.Exists(asmFile)) EasyDiagnostics.Print("good.size", new FileInfo(asmFile).Length);
      bool expected = report.CollisionCount == 0
        && report.FloatingFragmentCount == 0
        && report.FragmentCount == 2
        && report.GroundedFragmentCount == 2
        && report.FullyConstrainedFragmentCount == 2
        && report.EstimatedDofRemaining == 0;
      EasyDiagnostics.Print("good.expectedClean", expected);
      return expected ? asmFile : "";
    } finally {
      if (asm != null) sess.Close(asm);
    }
  }

  static string MakeTouchingAssembly(EasySession sess, string partFile) {
    Document asm = null;
    try {
      string asmFile = sess.ArtifactPath("assembly_validation_touching.grb");
      asm = sess.New3DDocument(false);
      asm.BeginChanges("touching assembly with fixed face contact");
      PointsLCS a = MakeLcs(asm, "TOUCH_A", 0, 0, 0);
      PointsLCS b = MakeLcs(asm, "TOUCH_B", 20, 0, 0);
      Fragment3D fragA = new Fragment3D(partFile, asm);
      fragA.Name = "touching_fragment_a";
      fragA.FixByFragmentLCS("FRAG_LCS", a);
      Fragment3D fragB = new Fragment3D(partFile, asm);
      fragB.Name = "touching_fragment_b";
      fragB.FixByFragmentLCS("FRAG_LCS", b);
      var end = asm.EndChanges();
      EasyDiagnostics.Print("touch.end", end);
      AssemblyValidationReport report = EasyAssemblyValidation.Validate(asm, "touch");
      bool saved = asm.SaveAs(asmFile);
      EasyDiagnostics.Print("touch.saved", saved);
      EasyDiagnostics.Print("touch.path", asmFile);
      EasyDiagnostics.Print("touch.exists", File.Exists(asmFile));
      if (File.Exists(asmFile)) EasyDiagnostics.Print("touch.size", new FileInfo(asmFile).Length);
      bool expected = report.CollisionCount == 0
        && report.ContactCount > 0
        && report.FloatingFragmentCount == 0
        && report.FragmentCount == 2
        && report.GroundedFragmentCount == 2
        && report.FullyConstrainedFragmentCount == 2
        && report.EstimatedDofRemaining == 0;
      EasyDiagnostics.Print("touch.expectedContact", expected);
      return expected ? asmFile : "";
    } finally {
      if (asm != null) sess.Close(asm);
    }
  }

  public static int Main() {
    using (var sess = EasySession.Start3D()) {
      try {
        string partFile = MakeSourcePart(sess);
        string badFile = MakeBadAssembly(sess, partFile);
        string goodFile = MakeGoodAssembly(sess, partFile);
        string touchFile = MakeTouchingAssembly(sess, partFile);
        bool ok = File.Exists(partFile) && File.Exists(badFile) && File.Exists(goodFile) && File.Exists(touchFile);
        EasyDiagnostics.Print("assemblyValidation.live", ok);
        return ok ? 0 : 20;
      } catch (Exception ex) {
        EasyDiagnostics.Print("exceptionType", ex.GetType().FullName);
        EasyDiagnostics.Print("exception", ex.Message);
        Console.WriteLine(ex.ToString());
        return 99;
      }
    }
  }
}
