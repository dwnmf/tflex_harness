using TFlex.Model;
using TFlex.Model.Model3D;
using TFlexEasy;

public class Program {
  public static int Main(){
    using (var sess = EasySession.Start3D()) {
      string partFile = EasyAssembly.CreatePartWithFragmentLcs(sess, "assembly_build_backlog_part.grb", "FRAG_LCS", 20.0);
      var asm = sess.New3DDocument(false);
      asm.BeginChanges("helper assembly build backlog");
      PointsLCS a = EasyAssembly.CreateTargetLcs(asm, "ASM_A", 0.0, 0.0, 0.0);
      PointsLCS b = EasyAssembly.CreateTargetLcs(asm, "ASM_B", 55.0, 0.0, 0.0);
      Fragment3D fixedA = EasyAssembly.InsertFixedFragment(asm, partFile, "FRAG_LCS", a, "fixed_a");
      Fragment3D fixedB = EasyAssembly.InsertFixedFragment(asm, partFile, "FRAG_LCS", b, "fixed_b");
      Fragment3D floating = EasyAssembly.InsertFloatingFragment(asm, partFile, "floating_c");
      var end = asm.EndChanges();
      EasyDiagnostics.Print("assembly.endChanges", end);
      if (end.ToString() != "OK") return 10;
      var options = new AssemblyValidationOptions();
      options.AllowContact = true;
      AssemblyValidationReport report = EasyAssemblyValidation.Validate(asm, "assemblyBacklog", options);
      EasyAssemblyValidation.WriteJsonSummary(report, sess.ArtifactPath("assembly_build_backlog_summary.json"));
      EasyMateInspector.PrintMates(asm);
      EasyMateInspector.PrintMateGeometryOwners(asm);
      EasyMateInspector.WriteMateGraph(asm, sess.ArtifactPath("assembly_build_backlog_mates.json"));
      EasyCommandProbe.ListKnownCommands();
      bool saved = EasyExport.Grb(asm, sess.ArtifactPath("assembly_build_backlog.grb"));
      bool expected = saved && report.FragmentCount == 3 && report.FloatingFragmentCount == 1 && report.CollisionCount == 1 && report.PolicyViolationCount == 1;
      EasyDiagnostics.Print("assemblyBacklog.expectedDetected", expected);
      return expected ? 0 : 20;
    }
  }
}
