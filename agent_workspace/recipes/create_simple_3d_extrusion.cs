using System;
using System.IO;
using TFlex;
using TFlex.Model;
using TFlex.Model.Model2D;
using TFlex.Model.Model3D;

public class Program {
  public static int Main(){
    string output = Environment.GetEnvironmentVariable("TFLEX_RECIPE_OUTPUT_FILE");
    if (String.IsNullOrWhiteSpace(output)) output = Path.GetFullPath("simple_3d_extrusion.grb");
    Directory.CreateDirectory(Path.GetDirectoryName(output));

    var setup = new ApplicationSessionSetup();
    setup.ReadOnly = false;
    setup.Enable3D = true;
    setup.EnableDOCs = false;
    setup.EnableMacros = false;
    setup.PromptToSaveModifiedDocuments = false;
    setup.ProtectionLicense = ApplicationSessionSetup.License.TFlex3D;

    bool init = Application.InitSession(setup);
    Console.WriteLine("init=" + init);
    if (!init) return 10;

    Document document = null;
    try {
      document = Application.NewDocument(true, false);
      Console.WriteLine("docNull=" + (document == null));
      if (document == null) return 11;

      int operationsBefore = Document3D.GetOperations(document).Count;
      Console.WriteLine("operationsBefore=" + operationsBefore);

      document.BeginChanges("create simple 3D extrusion");
      FreeNode center = new FreeNode(document, 1, 1);
      CircleConstruction circle = new CircleConstruction(document);
      circle.SetCenterAndRadius(center, 10);

      Area area = new Area(document);
      TFlex.Model.Model2D.Contour contour = area.AppendContour();
      ConstructionContourSegment segment = new ConstructionContourSegment(contour);
      segment.Construction = circle;

      StandardWorkplane workplane = new StandardWorkplane(document, StandardWorkplane.StandardType.Left);
      AreaProfile profile = new AreaProfile(document);
      profile.Area = area;
      profile.WorkSurface = workplane;

      ThickenExtrusion extrusion = new ThickenExtrusion(document);
      extrusion.Thickness1 = 10;
      extrusion.LengthType = ThickenExtrusion.LengthValue.AutoValue;
      extrusion.ForwardLength = 50;
      extrusion.Profile.Add(profile.Geometry.SheetContour);

      var end = document.EndChanges();
      Console.WriteLine("endChanges=" + end);

      int operationsAfter = Document3D.GetOperations(document).Count;
      Console.WriteLine("operationsAfter=" + operationsAfter);
      Console.WriteLine("operationType=" + extrusion.GetType().FullName);
      Console.WriteLine("bodyNull=" + (extrusion.Body == null));
      Console.WriteLine("geometryNull=" + (extrusion.Geometry == null));

      bool saved = document.SaveAs(output);
      Console.WriteLine("saved=" + saved);
      Console.WriteLine("exists=" + File.Exists(output));
      Console.WriteLine("output=" + output);

      if (end.ToString() != "OK") return 12;
      if (operationsAfter <= operationsBefore) return 13;
      if (extrusion.Body == null || extrusion.Geometry == null) return 14;
      if (!saved || !File.Exists(output)) return 15;
      return 0;
    } catch (Exception ex) {
      Console.WriteLine("exceptionType=" + ex.GetType().FullName);
      Console.WriteLine("exception=" + ex.Message);
      Console.WriteLine(ex.ToString());
      return 99;
    } finally {
      try { if (document != null) document.Close(); } catch (Exception closeEx) { Console.WriteLine("closeException=" + closeEx.Message); }
      if (Application.IsSessionInitialized) Application.ExitSession();
      Console.WriteLine("session=" + Application.IsSessionInitialized);
    }
  }
}
