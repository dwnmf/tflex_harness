using System;
using System.IO;
using TFlex.Model;
using TFlex.Model.Model3D;

namespace TFlexEasy {
  public static class EasyAssembly {
    public static PointsLCS CreateTargetLcs(Document doc, string name, double oxMm, double oyMm, double ozMm) {
      double ox = EasyUnits.MmToModel(oxMm);
      double oy = EasyUnits.MmToModel(oyMm);
      double oz = EasyUnits.MmToModel(ozMm);
      double axisLen = EasyUnits.MmToModel(10.0);
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
      EasyDiagnostics.Print(name + ".lcsCreated", true);
      EasyDiagnostics.Print(name + ".originMm", EasyUnits.F(oxMm) + "," + EasyUnits.F(oyMm) + "," + EasyUnits.F(ozMm));
      return lcs;
    }

    public static string CreatePartWithFragmentLcs(EasySession sess, string fileName, string lcsName, double blockSizeMm) {
      Document part = null;
      try {
        part = sess.New3DDocument(false);
        string path = sess.ArtifactPath(fileName);
        part.BeginChanges("easy assembly part with fragment lcs");
        EasySolids.BlockMm(part, blockSizeMm, blockSizeMm, blockSizeMm, 0.0, 0.0, 0.0, "fragment_source_block");
        CreateTargetLcs(part, lcsName, 0.0, 0.0, 0.0);
        var end = part.EndChanges();
        EasyDiagnostics.Print("assemblyBuild.part.endChanges", end);
        bool saved = EasyExport.Grb(part, path);
        EasyDiagnostics.Print("assemblyBuild.part.saved", saved);
        return path;
      } finally {
        if (part != null) sess.Close(part);
      }
    }

    public static Fragment3D InsertFixedFragment(Document asm, string partFile, string sourceLcsName, PointsLCS targetLcs, string name) {
      Fragment3D fragment = new Fragment3D(partFile, asm);
      fragment.Name = name;
      fragment.FixByFragmentLCS(sourceLcsName, targetLcs);
      EasyDiagnostics.Print(name + ".inserted", true);
      EasyDiagnostics.Print(name + ".fixedByLcs", true);
      EasyDiagnostics.Print(name + ".sourceLcs", sourceLcsName);
      EasyDiagnostics.Print(name + ".targetLcsNull", targetLcs == null);
      return fragment;
    }

    public static Fragment3D InsertFloatingFragment(Document asm, string partFile, string name) {
      Fragment3D fragment = new Fragment3D(partFile, asm);
      fragment.Name = name;
      EasyDiagnostics.Print(name + ".inserted", true);
      EasyDiagnostics.Print(name + ".fixedByLcs", false);
      return fragment;
    }

    public static bool SavePartAndAssembly(Document part, string partPath, Document assembly, string assemblyPath) {
      bool partSaved = part == null || EasyExport.Grb(part, partPath);
      bool assemblySaved = assembly == null || EasyExport.Grb(assembly, assemblyPath);
      EasyDiagnostics.Print("assemblyBuild.partPath", partPath);
      EasyDiagnostics.Print("assemblyBuild.assemblyPath", assemblyPath);
      EasyDiagnostics.Print("assemblyBuild.saved", partSaved && assemblySaved);
      return partSaved && assemblySaved;
    }
  }
}
