using System;
using TFlex.Model;
using TFlex.Model.Model3D;
using TFlexEasy;

public class Program {
  public static int Main(){
    using (var sess = EasySession.Start3D()) {
      var doc = sess.New3DDocument(false);
      doc.BeginChanges("parametric reconstruction from semantic model");
      EasyGearToothStyle style = EasyGearToothStyle.Clearanced;

      var p0 = EasyGears.ExternalTrapezoidGearWithBoreAt(doc, 0, 0, 24, 42, 54, 10, -7.50000001, style, "sun_24t_od54_bore10_clearanced_profile_parametric");
      EasySolids.ExtrudeMm(doc, p0, 0, 8, "sun_24t_od54_bore10_clearanced_parametric");

      var p1 = EasyGears.InternalTrapezoidGearRingAt(doc, 0, 0, 60, 140, 126, 114, -9, style, "ring_60t_od140_internal_clearanced_profile_parametric");
      EasySolids.ExtrudeMm(doc, p1, 0, 8, "ring_60t_od140_internal_clearanced_parametric");

      var p2 = EasyGears.CircleAt(doc, 0, 0, 105, 144, "carrier_plate_d105_z_minus5_minus1_clearanced_profile_parametric");
      EasySolids.ExtrudeMm(doc, p2, -5, 4, "carrier_plate_d105_z_minus5_minus1_clearanced_parametric");

      var p3 = EasyGears.ExternalTrapezoidGearAt(doc, 42, 0, 18, 31, 41, 180, style, "planet_1_18t_od41_clearanced_profile_parametric");
      EasySolids.ExtrudeMm(doc, p3, 0, 8, "planet_1_18t_od41_clearanced_parametric");

      var p4 = EasyGears.CircleAt(doc, 42, 0, 6, 48, "pin_1_d6_h14_clearanced_profile_parametric");
      EasySolids.ExtrudeMm(doc, p4, -5, 14, "pin_1_d6_h14_clearanced_parametric");

      var p5 = EasyGears.ExternalTrapezoidGearAt(doc, -21, 36.37306695, 18, 31, 41, -60, style, "planet_2_18t_od41_clearanced_profile_parametric");
      EasySolids.ExtrudeMm(doc, p5, 0, 8, "planet_2_18t_od41_clearanced_parametric");

      var p6 = EasyGears.CircleAt(doc, -21, 36.37306696, 6, 48, "pin_2_d6_h14_clearanced_profile_parametric");
      EasySolids.ExtrudeMm(doc, p6, -5, 14, "pin_2_d6_h14_clearanced_parametric");

      var p7 = EasyGears.ExternalTrapezoidGearAt(doc, -21, -36.37306697, 18, 31, 41, 60, style, "planet_3_18t_od41_clearanced_profile_parametric");
      EasySolids.ExtrudeMm(doc, p7, 0, 8, "planet_3_18t_od41_clearanced_parametric");

      var p8 = EasyGears.CircleAt(doc, -21, -36.37306696, 6, 48, "pin_3_d6_h14_clearanced_profile_parametric");
      EasySolids.ExtrudeMm(doc, p8, -5, 14, "pin_3_d6_h14_clearanced_parametric");

      var end = doc.EndChanges();
      EasyDiagnostics.Print("endChanges", end);
      if (end.ToString() != "OK") return 10;
      var operations = Document3D.GetOperations(doc);
      EasyDiagnostics.Print("operations", operations.Count);
      foreach (Operation op in operations) EasyDiagnostics.PrintBodyBoxMm(op.Name, op);
      bool grb = EasyExport.Grb(doc, sess.ArtifactPath("parametric_from_grb.grb"));
      EasyDiagnostics.Print("grbSaved", grb);
      bool step = EasyExport.Step(doc, sess.ArtifactPath("parametric_from_grb.step"));
      return (grb && step) ? 0 : 20;
    }
  }
}
