using System.IO;
using TFlex.Model;
using TFlex.Model.Model2D;
using TFlex.Model.Model3D;
using TFlexEasy;

public class Program {
  public static int Main(){
    using (var sess = EasySession.Start3D()) {
      var part = sess.New3DDocument(false);
      part.BeginChanges("export matrix 3d source");
      var block = EasySolids.BlockMm(part, 25.0, 20.0, 12.0, 0.0, 0.0, 0.0, "export_matrix_block");
      var end3d = part.EndChanges();
      EasyDiagnostics.Print("export3d.endChanges", end3d);
      if (end3d.ToString() != "OK") return 10;
      string partBase = sess.ArtifactPath("helper_export_matrix_part");
      bool partExports = EasyExport.All(part, partBase, true, true, false, false, false);
      bool partGrb = EasyExport.VerifyNonEmpty(partBase + ".grb");
      bool partStep = EasyExport.VerifyNonEmpty(partBase + ".stp");
      EasyDiagnostics.Print("export3d.allOk", partExports && partGrb && partStep);
      sess.Close(part);

      var drawing = sess.New2DDocument(false);
      drawing.BeginChanges("export matrix 2d source");
      FreeNode a = new FreeNode(drawing, 0, 0);
      FreeNode b = new FreeNode(drawing, 80, 30);
      LineConstruction line = new LineConstruction(drawing);
        line.SetThroughNodes(a, b);
      CircleConstruction circle = new CircleConstruction(drawing);
      circle.SetCenterAndRadius(a, 15);
      var end2d = drawing.EndChanges();
      EasyDiagnostics.Print("export2d.endChanges", end2d);
      if (end2d.ToString() != "OK") return 20;
      string drawingBase = sess.ArtifactPath("helper_export_matrix_drawing");
      bool drawingExports = EasyExport.All(drawing, drawingBase, true, false, true, true, true);
      bool drawingGrb = EasyExport.VerifyNonEmpty(drawingBase + ".grb");
      bool drawingDxf = EasyExport.VerifyNonEmpty(drawingBase + ".dxf");
      bool drawingDwg = EasyExport.VerifyNonEmpty(drawingBase + ".dwg");
      bool drawingPdf = EasyExport.VerifyNonEmpty(drawingBase + ".pdf");
      EasyDiagnostics.Print("export2d.allOk", drawingExports && drawingGrb && drawingDxf && drawingDwg && drawingPdf);
      sess.Close(drawing);

      bool ok = partExports && partGrb && partStep && drawingExports && drawingGrb && drawingDxf && drawingDwg && drawingPdf;
      EasyDiagnostics.Print("exportMatrix.expectedClean", ok);
      return ok ? 0 : 30;
    }
  }
}
