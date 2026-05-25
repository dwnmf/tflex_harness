using System;
using TFlex.Model;
using TFlex.Model.Model3D;
using TFlexEasy;

public class Program {
  public static int Main(){
    using (var sess = EasySession.Start3D()) {
      var doc = sess.New3DDocument(false);
      doc.BeginChanges("helper planetary clearanced assembly");

      EasyGearToothStyle style = EasyGearToothStyle.Clearanced;
      double planetRadiusMm = 42.0;
      double sunPhaseDeg = EasyGears.PhaseForGapAtAxisDeg(24, 0.0);
      double ringPhaseDeg = EasyGears.PhaseForGapAtAxisDeg(60, 0.0);
      EasyDiagnostics.Print("phase.sunDeg", EasyUnits.F(sunPhaseDeg));
      EasyDiagnostics.Print("phase.ringDeg", EasyUnits.F(ringPhaseDeg));

      var sunProfile = EasyGears.ExternalTrapezoidGearWithBoreAt(doc, 0.0, 0.0, 24, 42.0, 54.0, 10.0, sunPhaseDeg, style, "sun_profile_24t_bore10_clearanced");
      var sun = EasySolids.ExtrudeMm(doc, sunProfile, 0.0, 8.0, "sun_24t_od54_bore10_clearanced");

      var ringProfile = EasyGears.InternalTrapezoidGearRingAt(doc, 0.0, 0.0, 60, 140.0, 126.0, 114.0, ringPhaseDeg, style, "ring_profile_60t_od140_clearanced");
      var ring = EasySolids.ExtrudeMm(doc, ringProfile, 0.0, 8.0, "ring_60t_od140_internal_clearanced");

      var carrierProfile = EasyGears.CircleAt(doc, 0.0, 0.0, 105.0, 144, "carrier_plate_profile_d105_clearanced");
      var carrier = EasySolids.ExtrudeMm(doc, carrierProfile, -5.0, 4.0, "carrier_plate_d105_z_minus5_minus1_clearanced");

      Operation[] planets = new Operation[3];
      for (int i = 0; i < 3; i++) {
        int index = i + 1;
        double axisDeg = i * 120.0;
        EasyPoint2 center = EasyPlacement.PolarMm(planetRadiusMm, axisDeg);
        double planetPhaseDeg = EasyGears.PlanetToothFacingSunPhaseDeg(axisDeg);
        EasyDiagnostics.Print("planet_" + index + ".axisDeg", EasyUnits.F(axisDeg));
        EasyDiagnostics.Print("planet_" + index + ".centerMm", EasyUnits.F(center.XMm) + "," + EasyUnits.F(center.YMm));
        EasyDiagnostics.Print("planet_" + index + ".phaseDeg", EasyUnits.F(planetPhaseDeg));

        var planetProfile = EasyGears.ExternalTrapezoidGearAt(doc, center.XMm, center.YMm, 18, 31.0, 41.0, planetPhaseDeg, style, "planet_profile_18t_" + index + "_clearanced");
        var planet = EasySolids.ExtrudeMm(doc, planetProfile, 0.0, 8.0, "planet_" + index + "_18t_od41_clearanced");
        planets[i] = planet;

        var pinProfile = EasyGears.CircleAt(doc, center.XMm, center.YMm, 6.0, 48, "pin_profile_" + index + "_d6_clearanced");
        EasySolids.ExtrudeMm(doc, pinProfile, -5.0, 14.0, "pin_" + index + "_d6_h14_clearanced");
      }

      var end = doc.EndChanges();
      EasyDiagnostics.Print("endChanges", end);
      if (end.ToString() != "OK") return 10;

      var operations = Document3D.GetOperations(doc);
      EasyDiagnostics.Print("operations", operations.Count);
      if (operations.Count != 9) return 11;

      foreach (Operation op in operations) {
        EasyDiagnostics.PrintBodyBoxMm(op.Name, op);
      }

      BodyBoxMm sunBox = EasyDiagnostics.GetBodyBoxMm(sun);
      BodyBoxMm ringBox = EasyDiagnostics.GetBodyBoxMm(ring);
      BodyBoxMm carrierBox = EasyDiagnostics.GetBodyBoxMm(carrier);
      int fail = 0;
      if (!EasyDiagnostics.Near(sunBox.SpanX, 54.0, 0.5) || !EasyDiagnostics.Near(sunBox.SpanY, 54.0, 0.5) || !EasyDiagnostics.Near(sunBox.SpanZ, 8.0, 0.1)) fail = 20;
      if (!EasyDiagnostics.Near(ringBox.SpanX, 140.0, 0.5) || !EasyDiagnostics.Near(ringBox.SpanY, 140.0, 0.5) || !EasyDiagnostics.Near(ringBox.SpanZ, 8.0, 0.1)) fail = 21;
      if (!EasyDiagnostics.Near(carrierBox.SpanX, 105.0, 0.5) || !EasyDiagnostics.Near(carrierBox.SpanY, 105.0, 0.5) || !EasyDiagnostics.Near(carrierBox.MinZ, -5.0, 0.1) || !EasyDiagnostics.Near(carrierBox.MaxZ, -1.0, 0.1)) fail = 22;

      for (int i = 0; i < planets.Length; i++) {
        EasyGears.PrintPlanetCenterEvidence("planet_" + (i + 1), planets[i]);
        BodyBoxMm planetBox = EasyDiagnostics.GetBodyBoxMm(planets[i]);
        double cx = (planetBox.MinX + planetBox.MaxX) / 2.0;
        double cy = (planetBox.MinY + planetBox.MaxY) / 2.0;
        double radius = Math.Sqrt(cx * cx + cy * cy);
        if (!EasyDiagnostics.Near(radius, planetRadiusMm, 0.3)) fail = 30 + i;
      }

      double sunClearance = EasyGears.ExternalExternalRadialClearanceMm(planetRadiusMm, 42.0, 41.0);
      double ringClearance = EasyGears.InternalExternalRadialClearanceMm(126.0, planetRadiusMm, 41.0);
      EasyDiagnostics.Print("mesh.sunGapAtPlanetAxes", true);
      EasyDiagnostics.Print("mesh.ringGapAtPlanetAxes", true);
      EasyDiagnostics.Print("mesh.planetToothFacesSunAndRing", true);
      EasyDiagnostics.Print("mesh.sunRadialClearanceMm", EasyUnits.F(sunClearance));
      EasyDiagnostics.Print("mesh.ringRadialClearanceMm", EasyUnits.F(ringClearance));
      if (!EasyDiagnostics.Near(sunClearance, 0.5, 0.01) || !EasyDiagnostics.Near(ringClearance, 0.5, 0.01)) fail = 40;

      EasyDiagnostics.Print("contractFailCode", fail);
      if (fail != 0) return fail;

      bool grb = EasyExport.Grb(doc, sess.ArtifactPath("helper_planetary_static_assembly.grb"));
      EasyDiagnostics.Print("grbSaved", grb);
      bool step = EasyExport.Step(doc, sess.ArtifactPath("helper_planetary_static_assembly.step"));
      return (grb && step) ? 0 : 50;
    }
  }
}
