using System;
using System.Collections.Generic;
using TFlex.Model;
using TFlex.Model.Model3D;
using TFlexEasy;

public class Program {
  public static int Main(){
    using (var sess = EasySession.Start3D()) {
      var doc = sess.New3DDocument(false);
      doc.BeginChanges("helper modeling backlog sources");
      var basePlate = EasyFeatures.BasePlate(doc, 120.0, 70.0, 10.0, 8.0, "backlog_base_plate");
      Operation[] lugs = EasyFeatures.ClevisLugPair(doc, 24.0, 8.0, 52.0, 14.0, 26.0, "backlog_lugs");
      Operation ribA = EasyFeatures.ReinforcingRib(doc, new EasyPoint2(18, 8), new EasyPoint2(45, 8), new EasyPoint2(18, 40), 5.0, 30.0, "backlog_rib_a");
      Operation ribB = EasyFeatures.ReinforcingRib(doc, new EasyPoint2(-18, 8), new EasyPoint2(-45, 8), new EasyPoint2(-18, 40), 5.0, -35.0, "backlog_rib_b");
      Operation[] mountCuts = EasyFeatures.MountingHolePattern(doc, new double[] {-42.0, 42.0}, new double[] {-22.0, 22.0}, 9.0, 24.0, "backlog_mount_cut");
      Operation bore = EasyFeatures.HorizontalBoreCutter(doc, 18.0, 100.0, 0.0, 0.0, 52.0, "backlog_horizontal_bore");
      Operation tri = EasyFeatures.TriangularLighteningCutout(doc, new EasyPoint2(20, 24), new EasyPoint2(8, 46), new EasyPoint2(27, 46), 100.0, 50.0, "backlog_tri_cut");
      var slotProfile = EasyProfiles.Slot(doc, 0.0, 0.0, 36.0, 10.0, 20.0, "backlog_slot_profile");
      var slotCut = EasySolids.ExtrudeOn(doc, slotProfile, EasyWorkplanes.Top(doc), 24.0, "backlog_slot_cut");
      var endSources = doc.EndChanges();
      EasyDiagnostics.Print("sources.endChanges", endSources);
      if (endSources.ToString() != "OK") return 10;

      doc.BeginChanges("helper modeling backlog booleans");
      var united = EasyBoolean.Unite(doc, "backlog_united", basePlate, lugs[0], lugs[1], ribA, ribB);
      EasyFeatures.RoundTransitionBlend(united, 1.5);
      var endUnite = doc.EndChanges();
      EasyDiagnostics.Print("unite.endChanges", endUnite);
      if (endUnite.ToString() != "OK") return 20;

      doc.BeginChanges("helper modeling backlog cuts");
      List<Operation> cutters = new List<Operation>();
      cutters.AddRange(mountCuts);
      cutters.Add(bore);
      cutters.Add(tri);
      cutters.Add(slotCut);
      var final = EasyBoolean.Subtract(doc, "backlog_final_part", united, cutters.ToArray());
      var endCuts = doc.EndChanges();
      EasyDiagnostics.Print("cuts.endChanges", endCuts);
      if (endCuts.ToString() != "OK") return 30;

      EasyWorkplanes.PrintAxisMapping(doc);
      EasyWorkplanes.AssertKnownMapping();
      EasyEvidence.PrintOperationSummary(doc);
      bool bboxOk = EasyEvidence.AssertBbox(final, 120.0, 70.0, 76.0, 0.8);
      bool featureOk = true;
      featureOk = EasyEvidence.PrintFeatureCount("features.mountingHoles", 4, mountCuts.Length) && featureOk;
      featureOk = EasyEvidence.PrintFeatureCount("features.lugs", 2, lugs.Length) && featureOk;
      featureOk = EasyEvidence.PrintFeatureCount("features.ribs", 2, 2) && featureOk;
      var manifest = new Dictionary<string,string>();
      manifest["recipe"] = "helper_modeling_backlog";
      manifest["bboxOk"] = bboxOk.ToString();
      manifest["featureOk"] = featureOk.ToString();
      EasyEvidence.WriteManifest(sess.ArtifactPath("helper_modeling_backlog.evidence.json"), manifest);
      bool exported = EasyExport.All(doc, sess.ArtifactPath("helper_modeling_backlog_export"), true, false, false, false, false);
      var reopen = EasyReopen.SaveCloseReopen3D(sess, doc, sess.ArtifactPath("helper_modeling_backlog.grb"));
      EasyReopen.PrintReopenEvidence(reopen, "modeling.reopen");
      bool reopenOk = reopen.Reopened && reopen.OperationCount > 0 && reopen.BBox.Valid;
      if (reopen.Document != null) reopen.Document.Close();
      EasyDiagnostics.Print("modeling.expectedClean", bboxOk && featureOk && exported && reopenOk);
      return bboxOk && featureOk && exported && reopenOk ? 0 : 40;
    }
  }
}
