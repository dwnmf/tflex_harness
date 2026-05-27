using System;
using System.Collections;
using TFlex.Model;
using TFlex.Model.Model3D;
using TFlex.Model.Model3D.Geometry;

namespace TFlexEasy {
  public static class EasyNativeMates {
    public static ModelBody FirstSolidBody(Operation op) {
      if (op == null || op.Geometry == null || op.Geometry.Solid == null || op.Geometry.Solid.Length <= 0) return null;
      return op.Geometry.Solid[0] as ModelBody;
    }

    public static ModelBody FirstSolidBody(Fragment3D fragment) {
      if (fragment == null || fragment.Geometry == null || fragment.Geometry.Solid == null || fragment.Geometry.Solid.Length <= 0) return null;
      return fragment.Geometry.Solid[0] as ModelBody;
    }

    public static ModelFace Face(Operation op, int index) {
      ModelBody body = FirstSolidBody(op);
      if (body == null) return null;
      return Nth(body.Faces, index) as ModelFace;
    }

    public static ModelFace Face(Fragment3D op, int index) {
      ModelBody body = FirstSolidBody(op);
      if (body == null) return null;
      return Nth(body.Faces, index) as ModelFace;
    }

    public static ModelEdge Edge(Operation op, int index) {
      ModelBody body = FirstSolidBody(op);
      if (body == null) return null;
      return Nth(body.Edges, index) as ModelEdge;
    }

    public static ModelEdge Edge(Fragment3D op, int index) {
      ModelBody body = FirstSolidBody(op);
      if (body == null) return null;
      return Nth(body.Edges, index) as ModelEdge;
    }

    public static Mate ConcentricByEdgeAxis(Document doc, Operation first, Operation second, int edgeIndex, string name) {
      ModelEdge edge1 = Edge(first, edgeIndex);
      ModelEdge edge2 = Edge(second, edgeIndex);
      Geometry geom1 = edge1 == null || edge1.Geometry == null ? null : edge1.Geometry.Axis;
      Geometry geom2 = edge2 == null || edge2.Geometry == null ? null : edge2.Geometry.Axis;
      return Create(doc, name, Mate.MateType.Concentricity, geom1, geom2);
    }

    public static Mate ConcentricByEdgeAxis(Document doc, Fragment3D first, Fragment3D second, int edgeIndex, string name) {
      ModelEdge edge1 = Edge(first, edgeIndex);
      ModelEdge edge2 = Edge(second, edgeIndex);
      Geometry geom1 = edge1 == null || edge1.Geometry == null ? null : edge1.Geometry.Axis;
      Geometry geom2 = edge2 == null || edge2.Geometry == null ? null : edge2.Geometry.Axis;
      return Create(doc, name, Mate.MateType.Concentricity, geom1, geom2);
    }

    public static Mate CoincidentByFaceSurface(Document doc, Operation first, Operation second, int faceIndex, string name) {
      ModelFace face1 = Face(first, faceIndex);
      ModelFace face2 = Face(second, faceIndex);
      Geometry geom1 = face1 == null || face1.Geometry == null ? null : face1.Geometry.Surface;
      Geometry geom2 = face2 == null || face2.Geometry == null ? null : face2.Geometry.Surface;
      return Create(doc, name, Mate.MateType.Coincidence, geom1, geom2);
    }

    public static Mate CoincidentByFaceSurface(Document doc, Fragment3D first, Fragment3D second, int faceIndex, string name) {
      ModelFace face1 = Face(first, faceIndex);
      ModelFace face2 = Face(second, faceIndex);
      Geometry geom1 = face1 == null || face1.Geometry == null ? null : face1.Geometry.Surface;
      Geometry geom2 = face2 == null || face2.Geometry == null ? null : face2.Geometry.Surface;
      return Create(doc, name, Mate.MateType.Coincidence, geom1, geom2);
    }

    public static Mate CoincidentByFacePlane(Document doc, Operation first, Operation second, int faceIndex, string name) {
      ModelFace face1 = Face(first, faceIndex);
      ModelFace face2 = Face(second, faceIndex);
      Geometry geom1 = face1 == null || face1.Geometry == null ? null : face1.Geometry.Plane;
      Geometry geom2 = face2 == null || face2.Geometry == null ? null : face2.Geometry.Plane;
      return Create(doc, name, Mate.MateType.Coincidence, geom1, geom2);
    }

    public static Mate CoincidentByFacePlane(Document doc, Fragment3D first, Fragment3D second, int faceIndex, string name) {
      ModelFace face1 = Face(first, faceIndex);
      ModelFace face2 = Face(second, faceIndex);
      Geometry geom1 = face1 == null || face1.Geometry == null ? null : face1.Geometry.Plane;
      Geometry geom2 = face2 == null || face2.Geometry == null ? null : face2.Geometry.Plane;
      return Create(doc, name, Mate.MateType.Coincidence, geom1, geom2);
    }

    public static Mate Create(Document doc, string name, Mate.MateType type, Geometry element1, Geometry element2) {
      Mate mate = new Mate(doc);
      if (!String.IsNullOrWhiteSpace(name)) mate.Name = name;
      mate.Type = type;
      mate.Element1 = element1;
      mate.Element2 = element2;
      EasyDiagnostics.Print(name + ".mateType", type);
      EasyDiagnostics.Print(name + ".element1Null", element1 == null);
      EasyDiagnostics.Print(name + ".element2Null", element2 == null);
      return mate;
    }

    static object Nth(IEnumerable source, int index) {
      if (source == null || index < 0) return null;
      int current = 0;
      foreach (object item in source) {
        if (item == null) continue;
        if (current == index) return item;
        current++;
      }
      return null;
    }
  }
}
