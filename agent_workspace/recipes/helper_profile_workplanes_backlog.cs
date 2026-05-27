using System;
using System.Collections.Generic;
using TFlex.Model;
using TFlex.Model.Model3D;
using TFlexEasy;

public class Program {
  public static int Main(){
    using (var sess = EasySession.Start3D()) {
      var doc = sess.New3DDocument(false);
      doc.BeginChanges("profile workplane matrix");
      int created = 0;
      created += AddProfileSet(doc, StandardWorkplane.StandardType.Top, "top", 4.0);
      created += AddProfileSet(doc, StandardWorkplane.StandardType.Front, "front", 5.0);
      created += AddProfileSet(doc, StandardWorkplane.StandardType.Left, "left", 6.0);
      var end = doc.EndChanges();
      EasyDiagnostics.Print("profiles.endChanges", end);
      if (end.ToString() != "OK") return 10;

      EasyWorkplanes.PrintAxisMapping(doc);
      int valid = 0;
      int positive = 0;
      foreach (Operation op in Document3D.GetOperations(doc)) {
        BodyBoxMm box = EasyDiagnostics.PrintBodyBoxMm("profiles." + op.Name, op);
        if (box.Valid) valid++;
        if (box.Valid && box.SpanX > 0 && box.SpanY > 0 && box.SpanZ > 0) positive++;
      }
      int operations = Document3D.GetOperations(doc).Count;
      EasyDiagnostics.Print("profiles.created", created);
      EasyDiagnostics.Print("profiles.operations", operations);
      EasyDiagnostics.Print("profiles.validBbox", valid);
      EasyDiagnostics.Print("profiles.positiveBbox", positive);
      EasyEvidence.PrintFeatureCount("profiles.expectedOperations", 24, operations);
      bool saved = EasyExport.Grb(doc, sess.ArtifactPath("helper_profile_workplanes_backlog.grb"));
      bool ok = created == 24 && operations == 24 && valid == 24 && positive == 24 && saved;
      EasyDiagnostics.Print("profiles.expectedClean", ok);
      return ok ? 0 : 20;
    }
  }

  static int AddProfileSet(Document doc, StandardWorkplane.StandardType plane, string prefix, double height) {
    int count = 0;
    Add(doc, plane, prefix, "polygon", MakePolygon(doc, prefix + "_polygon"), height); count++;
    Add(doc, plane, prefix, "rectangle", EasyProfiles.Rectangle(doc, 0, 0, 18, 10, prefix + "_rectangle_profile"), height); count++;
    Add(doc, plane, prefix, "rounded_rectangle", EasyProfiles.RoundedRectangle(doc, 0, 0, 20, 12, 3, prefix + "_rounded_rectangle_profile"), height); count++;
    Add(doc, plane, prefix, "triangle", EasyProfiles.Triangle(doc, new EasyPoint2(-8, -5), new EasyPoint2(9, -4), new EasyPoint2(1, 10), prefix + "_triangle_profile"), height); count++;
    Add(doc, plane, prefix, "slot", EasyProfiles.Slot(doc, 0, 0, 24, 8, 25, prefix + "_slot_profile"), height); count++;
    Add(doc, plane, prefix, "obround", EasyProfiles.Obround(doc, 0, 0, 22, 7, -20, prefix + "_obround_profile"), height); count++;
    Add(doc, plane, prefix, "lug", EasyProfiles.LugProfile(doc, 8, -6, 7, prefix + "_lug_profile"), height); count++;
    Add(doc, plane, prefix, "with_hole", MakeWithHole(doc, prefix + "_with_hole_profile"), height); count++;
    return count;
  }

  static void Add(Document doc, StandardWorkplane.StandardType plane, string prefix, string label, AreaProfile profile, double height) {
    var op = EasySolids.ExtrudeOn(doc, profile, new StandardWorkplane(doc, plane), height, prefix + "_" + label);
    EasyDiagnostics.Print(prefix + "." + label + ".profile", true);
    EasyDiagnostics.Print(prefix + "." + label + ".workplane", plane);
    EasyDiagnostics.Print(prefix + "." + label + ".heightMm", EasyUnits.F(height));
  }

  static AreaProfile MakePolygon(Document doc, string name) {
    return EasyProfiles.Polygon(doc, new EasyPoint2[] {
      new EasyPoint2(-8,-5), new EasyPoint2(6,-6), new EasyPoint2(10,1), new EasyPoint2(1,9), new EasyPoint2(-9,4)
    }, name);
  }

  static AreaProfile MakeWithHole(Document doc, string name) {
    var outer = new List<EasyPoint2>{ new EasyPoint2(-10,-8), new EasyPoint2(10,-8), new EasyPoint2(10,8), new EasyPoint2(-10,8) };
    var inner = new List<EasyPoint2>();
    for (int i=0; i<32; i++) {
      double a = 2.0 * Math.PI * i / 32;
      inner.Add(new EasyPoint2(3.0 * Math.Cos(a), 3.0 * Math.Sin(a)));
    }
    return EasyProfiles.WithHole(doc, outer, inner, name);
  }
}
