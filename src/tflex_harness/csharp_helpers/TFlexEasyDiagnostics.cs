using System;
using TFlex.Model.Model3D;

namespace TFlexEasy {
  public struct BodyBoxMm {
    public bool Valid;
    public double MinX;
    public double MinY;
    public double MinZ;
    public double MaxX;
    public double MaxY;
    public double MaxZ;
    public double SpanX;
    public double SpanY;
    public double SpanZ;
  }

  public static class EasyDiagnostics {
    public static void Print(string key, object value) {
      Console.WriteLine(key + "=" + (value == null ? "null" : value.ToString()));
    }

    public static bool Near(double actual, double expected, double tolerance) {
      return Math.Abs(actual - expected) <= tolerance;
    }

    public static int FailIf(bool condition, int code, string message) {
      if (condition) {
        Print("fail", message);
        return code;
      }
      return 0;
    }

    public static BodyBoxMm PrintBodyBoxMm(string label, Operation op) {
      BodyBoxMm box = GetBodyBoxMm(op);
      Print(label + ".bboxValid", box.Valid);
      Print(label + ".bboxMinMm", EasyUnits.F(box.MinX) + "," + EasyUnits.F(box.MinY) + "," + EasyUnits.F(box.MinZ));
      Print(label + ".bboxMaxMm", EasyUnits.F(box.MaxX) + "," + EasyUnits.F(box.MaxY) + "," + EasyUnits.F(box.MaxZ));
      Print(label + ".bboxSpanMm", EasyUnits.F(box.SpanX) + "," + EasyUnits.F(box.SpanY) + "," + EasyUnits.F(box.SpanZ));
      return box;
    }

    public static BodyBoxMm GetBodyBoxMm(Operation op) {
      BodyBoxMm result = new BodyBoxMm();
      if (op == null || op.Geometry == null) return result;
      var raw = op.Geometry.AABoundBox;
      result.Valid = raw.Valid;
      if (!raw.Valid) return result;
      double minX = EasyUnits.ModelToMm(raw.Minimum.X);
      double minY = EasyUnits.ModelToMm(raw.Minimum.Y);
      double minZ = EasyUnits.ModelToMm(raw.Minimum.Z);
      double maxX = EasyUnits.ModelToMm(raw.Maximum.X);
      double maxY = EasyUnits.ModelToMm(raw.Maximum.Y);
      double maxZ = EasyUnits.ModelToMm(raw.Maximum.Z);
      result.MinX = Math.Min(minX, maxX);
      result.MinY = Math.Min(minY, maxY);
      result.MinZ = Math.Min(minZ, maxZ);
      result.MaxX = Math.Max(minX, maxX);
      result.MaxY = Math.Max(minY, maxY);
      result.MaxZ = Math.Max(minZ, maxZ);
      result.SpanX = result.MaxX - result.MinX;
      result.SpanY = result.MaxY - result.MinY;
      result.SpanZ = result.MaxZ - result.MinZ;
      return result;
    }
  }
}
