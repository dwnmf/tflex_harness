
using System;
using System.IO;
using System.Text;
using TFlex;
using TFlex.Model;
using TFlex.Model.Model2D;
using TFlex.Model.Model3D;
using TFlexEasy;

public class Program {
  public static int Main(){
    using (var sess = EasySession.Start3D()) {
      string input = @"D:\REALPROJECTS\tflex_harness\artifacts\runs\20260525_124700_025877_recipe_helper_planetary_static_assembly\artifacts\helper_planetary_static_assembly.grb";
      Document doc = Application.OpenDocument(input, false, true);
      EasyDiagnostics.Print("docNull", doc == null);
      if (doc == null) return 10;
      var ops = Document3D.GetOperations(doc);
      EasyDiagnostics.Print("operations", ops.Count);
      StringBuilder json = new StringBuilder();
      json.Append("{\n  \"source_grb\": \"").Append(Escape(input)).Append("\",\n");
      json.Append("  \"operation_count\": ").Append(ops.Count).Append(",\n  \"operations\": [\n");
      int i = 0;
      foreach (Operation op in ops) {
        if (i > 0) json.Append(",\n");
        BodyBoxMm b = EasyDiagnostics.GetBodyBoxMm(op);
        ThickenExtrusion te = op as ThickenExtrusion;
        EasyDiagnostics.Print("op." + i + ".name", op.Name);
        EasyDiagnostics.PrintBodyBoxMm("op." + i, op);
        json.Append("    {");
        AddJsonProp(json, "index", i.ToString(), false); json.Append(",");
        AddJsonProp(json, "name", op.Name, true); json.Append(",");
        AddJsonProp(json, "type", op.GetType().FullName, true); json.Append(",");
        json.Append("\"bbox\": {\"min\": [").Append(F(b.MinX)).Append(", ").Append(F(b.MinY)).Append(", ").Append(F(b.MinZ)).Append("], ");
        json.Append("\"max\": [").Append(F(b.MaxX)).Append(", ").Append(F(b.MaxY)).Append(", ").Append(F(b.MaxZ)).Append("], ");
        json.Append("\"span\": [").Append(F(b.SpanX)).Append(", ").Append(F(b.SpanY)).Append(", ").Append(F(b.SpanZ)).Append("]},");
        json.Append("\"z_min_mm\": ").Append(F(b.MinZ)).Append(",");
        json.Append("\"height_mm\": ").Append(F(b.SpanZ)).Append(",");
        json.Append("\"contours\": [");
        int contourWritten = 0;
        if (te != null && te.Profile != null && te.Profile.Length > 0) {
          object modelContour = te.Profile[0];
          object owner = modelContour.GetType().GetProperty("Owner").GetValue(modelContour, null);
          Area area = owner.GetType().GetProperty("Area").GetValue(owner, null) as Area;
          if (area != null) {
            for (int ci = 0; ci < area.ContourCount; ci++) {
              Contour contour = area.GetContour(ci);
              for (int si = 0; si < contour.SegmentCount; si++) {
                ContourSegment segment = contour.GetSegment(si);
                OutlineContourSegment outlineSegment = segment as OutlineContourSegment;
                PolylineGeometry poly = null;
                object geomObj = segment.GetType().GetProperty("Geometry").GetValue(segment, null);
                poly = geomObj as PolylineGeometry;
                if (poly == null) continue;
                if (contourWritten > 0) json.Append(",");
                bool direction = outlineSegment == null ? true : outlineSegment.Direction;
                json.Append("{\"contour_index\": ").Append(ci).Append(", \"segment_index\": ").Append(si).Append(", \"direction\": ").Append(direction ? "true" : "false").Append(", \"points\": [");
                for (int pi = 0; pi < poly.Count; pi++) {
                  if (pi > 0) json.Append(",");
                  json.Append("[").Append(F(poly.GetX(pi))).Append(", ").Append(F(poly.GetY(pi))).Append("]");
                }
                json.Append("]}");
                contourWritten++;
              }
            }
          }
        }
        json.Append("]}");
        i++;
      }
      json.Append("\n  ]\n}\n");
      string path = sess.ArtifactPath("model_evidence_with_contours.json");
      File.WriteAllText(path, json.ToString(), Encoding.UTF8);
      EasyDiagnostics.Print("evidencePath", path);
      try { doc.Close(); } catch {}
      return 0;
    }
  }

  static void AddJsonProp(StringBuilder json, string name, string value, bool quote) {
    json.Append("\"").Append(name).Append("\": ");
    if (quote) json.Append("\"").Append(Escape(value)).Append("\""); else json.Append(value);
  }
  static string F(double value) { return value.ToString("0.########", System.Globalization.CultureInfo.InvariantCulture); }
  static string Escape(string value) { return (value ?? "").Replace("\\", "\\\\").Replace("\"", "\\\"").Replace("\r", "\\r").Replace("\n", "\\n"); }
}
