using TFlex.Model;
using TFlex.Model.Model3D;
using TFlexEasy;

public class Program {
  public static int Main(){
    using (var sess = EasySession.Start3D()) {
      var doc = sess.New3DDocument(false);
      doc.BeginChanges("solid primitive axis matrix");
      Operation block = EasySolids.BlockMm(doc, 12.0, 14.0, 16.0, 0.0, 0.0, 0.0, "primitive_block");
      Operation cylX = EasySolids.CylinderMm(doc, 6.0, 30.0, 50.0, 0.0, 0.0, "X", "primitive_cylinder_x");
      Operation cylY = EasySolids.CylinderMm(doc, 6.0, 30.0, 0.0, 50.0, 0.0, "Y", "primitive_cylinder_y");
      Operation cylZ = EasySolids.CylinderMm(doc, 6.0, 30.0, 0.0, 0.0, 50.0, "Z", "primitive_cylinder_z");
      Operation cutter = EasySolids.CutCylinderThrough(doc, 5.0, 36.0, -50.0, 0.0, 0.0, "X", "primitive_cut_x");
      EasySolids.NamedCutter(cutter, "primitive_named_cutter");
      var end = doc.EndChanges();
      EasyDiagnostics.Print("primitives.endChanges", end);
      if (end.ToString() != "OK") return 10;

      BodyBoxMm blockBox = EasyDiagnostics.PrintBodyBoxMm("primitives.block", block);
      BodyBoxMm xBox = EasyDiagnostics.PrintBodyBoxMm("primitives.cylinderX", cylX);
      BodyBoxMm yBox = EasyDiagnostics.PrintBodyBoxMm("primitives.cylinderY", cylY);
      BodyBoxMm zBox = EasyDiagnostics.PrintBodyBoxMm("primitives.cylinderZ", cylZ);
      BodyBoxMm cutterBox = EasyDiagnostics.PrintBodyBoxMm("primitives.namedCutter", cutter);
      bool blockOk = Positive(blockBox);
      bool xOk = AxisDominates(xBox, "X") && CenterNear(xBox, 50.0, 0.0, 0.0);
      bool yOk = AxisDominates(yBox, "Y") && CenterNear(yBox, 0.0, 50.0, 0.0);
      bool zOk = AxisDominates(zBox, "Z") && CenterNear(zBox, 0.0, 0.0, 50.0);
      bool cutterOk = AxisDominates(cutterBox, "X") && CenterNear(cutterBox, -50.0, 0.0, 0.0);
      EasyDiagnostics.Print("primitives.block.ok", blockOk);
      EasyDiagnostics.Print("primitives.axisX.ok", xOk);
      EasyDiagnostics.Print("primitives.axisY.ok", yOk);
      EasyDiagnostics.Print("primitives.axisZ.ok", zOk);
      EasyDiagnostics.Print("primitives.namedCutter.ok", cutterOk);
      EasyEvidence.PrintFeatureCount("primitives.operationCount", 5, Document3D.GetOperations(doc).Count);
      bool saved = EasyExport.Grb(doc, sess.ArtifactPath("helper_solid_primitives_backlog.grb"));
      bool ok = blockOk && xOk && yOk && zOk && cutterOk && saved;
      EasyDiagnostics.Print("primitives.expectedClean", ok);
      return ok ? 0 : 20;
    }
  }

  static bool Positive(BodyBoxMm box) {
    return box.Valid && box.SpanX > 0.0 && box.SpanY > 0.0 && box.SpanZ > 0.0;
  }

  static bool AxisDominates(BodyBoxMm box, string axis) {
    if (!Positive(box)) return false;
    if (axis == "X") return box.SpanX > box.SpanY * 2.0 && box.SpanX > box.SpanZ * 2.0;
    if (axis == "Y") return box.SpanY > box.SpanX * 2.0 && box.SpanY > box.SpanZ * 2.0;
    if (axis == "Z") return box.SpanZ > box.SpanX * 2.0 && box.SpanZ > box.SpanY * 2.0;
    return false;
  }

  static bool CenterNear(BodyBoxMm box, double xMm, double yMm, double zMm) {
    if (!box.Valid) return false;
    double cx = (box.MinX + box.MaxX) / 2.0;
    double cy = (box.MinY + box.MaxY) / 2.0;
    double cz = (box.MinZ + box.MaxZ) / 2.0;
    return System.Math.Abs(cx - xMm) <= 0.01 && System.Math.Abs(cy - yMm) <= 0.01 && System.Math.Abs(cz - zMm) <= 0.01;
  }
}
