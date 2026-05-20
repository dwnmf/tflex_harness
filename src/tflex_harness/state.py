from __future__ import annotations

import re
from typing import Any

from .runner import run_csharp_snippet

CAPTURE_STATE_CODE = r'''
using System;
using System.Collections;
using System.Collections.Generic;
using System.Globalization;
using System.Reflection;
using TFlex;
using TFlex.Model;
using TFlex.Model.Model2D;
using TFlex.Model.Model3D;

public class Program {
  public static int Main(){
    var setup = new ApplicationSessionSetup();
    setup.ReadOnly = true;
    setup.Enable3D = true;
    setup.EnableDOCs = false;
    setup.EnableMacros = false;
    setup.PromptToSaveModifiedDocuments = false;
    setup.ProtectionLicense = ApplicationSessionSetup.License.Auto;
    bool init = Application.InitSession(setup);
    Console.WriteLine("init=" + init);
    if (!init) return 10;
    try {
      var active = Application.ActiveDocument;
      Console.WriteLine("activeNull=" + (active == null));
      if (active != null) Console.WriteLine("active=" + Encode(active.Title) + "|" + Encode(active.FileName));
      int count = 0;
      foreach (Document doc in Application.Documents) {
        int index = count;
        count++;
        WriteDocument(index, doc);
      }
      Console.WriteLine("documents=" + count);
      return 0;
    } finally {
      if (Application.IsSessionInitialized) Application.ExitSession();
      Console.WriteLine("session=" + Application.IsSessionInitialized);
    }
  }

  static void WriteDocument(int index, Document doc) {
    int objects2d = Count2D(doc, index);
    int operations3d = Count3DOperations(doc, index);
    int variables = CountVariables(doc);
    Console.WriteLine("doc=" + index + "|" + Encode(doc.Title) + "|" + Encode(doc.FileName) + "|" + Encode(doc.FilePath) + "|" + objects2d + "|" + operations3d + "|" + variables + "|" + doc.Changed);
  }

  static int Count2D(Document doc, int docIndex) {
    try {
      Dictionary<string, int> types = new Dictionary<string, int>();
      int count = 0;
      foreach (Object2D obj in doc.Get2DObjects()) {
        count++;
        string type = obj.GetType().FullName;
        if (!types.ContainsKey(type)) types[type] = 0;
        types[type]++;
      }
      foreach (KeyValuePair<string, int> item in types) Console.WriteLine("object2dType=" + docIndex + "|" + item.Key + "|" + item.Value);
      return count;
    } catch (Exception ex) {
      Console.WriteLine("object2dError=" + docIndex + "|" + Encode(ex.GetType().FullName) + "|" + Encode(ex.Message));
      return -1;
    }
  }

  static int Count3DOperations(Document doc, int docIndex) {
    try {
      ICollection<Operation> operations = Document3D.GetOperations(doc);
      Dictionary<string, int> types = new Dictionary<string, int>();
      int index = 0;
      foreach (Operation op in operations) {
        string type = op.GetType().FullName;
        if (!types.ContainsKey(type)) types[type] = 0;
        types[type]++;
        WriteOperation(docIndex, index, op, type);
        index++;
      }
      foreach (KeyValuePair<string, int> item in types) Console.WriteLine("operation3dType=" + docIndex + "|" + item.Key + "|" + item.Value);
      return operations.Count;
    } catch (Exception ex) {
      Console.WriteLine("operation3dError=" + docIndex + "|" + Encode(ex.GetType().FullName) + "|" + Encode(ex.Message));
      return -1;
    }
  }

  static void WriteOperation(int docIndex, int opIndex, Operation op, string type) {
    try {
      var geometry = op.Geometry;
      var box = geometry == null ? null : geometry.AABoundBox;
      if (box == null || !box.Valid) {
        Console.WriteLine("operation3d=" + docIndex + "|" + opIndex + "|" + type + "|False||||");
        return;
      }
      double sizeX = Math.Abs(box.Maximum.X - box.Minimum.X);
      double sizeY = Math.Abs(box.Maximum.Y - box.Minimum.Y);
      double sizeZ = Math.Abs(box.Maximum.Z - box.Minimum.Z);
      Console.WriteLine("operation3d=" + docIndex + "|" + opIndex + "|" + type + "|True|" + FormatPoint(box.Minimum) + "|" + FormatPoint(box.Maximum) + "|" + FormatNumber(sizeX) + "," + FormatNumber(sizeY) + "," + FormatNumber(sizeZ));
    } catch (Exception ex) {
      Console.WriteLine("operation3d=" + docIndex + "|" + opIndex + "|" + type + "|False||||" + Encode(ex.Message));
    }
  }

  static int CountVariables(Document doc) {
    try {
      MethodInfo method = doc.GetType().GetMethod("GetVariables", Type.EmptyTypes);
      if (method == null) return -1;
      object variables = method.Invoke(doc, null);
      int count = 0;
      IEnumerable enumerable = variables as IEnumerable;
      if (enumerable == null) return -1;
      foreach (object ignored in enumerable) count++;
      return count;
    } catch {
      return -1;
    }
  }

  static string FormatPoint(TFlex.Model.Model3D.Geometry.BasePoint3D point){
    return FormatNumber(point.X) + "," + FormatNumber(point.Y) + "," + FormatNumber(point.Z);
  }

  static string FormatNumber(double value){
    return value.ToString(CultureInfo.InvariantCulture);
  }

  static string Encode(string value) {
    if (value == null) return "";
    return value.Replace("\\", "\\\\").Replace("|", "\\p").Replace("\r", "\\r").Replace("\n", "\\n");
  }
}
'''


def _parse_bool(value: str) -> bool | None:
    if value == "True":
        return True
    if value == "False":
        return False
    return None


def _decode(value: str) -> str:
    result = []
    escaped = False
    for char in value:
        if escaped:
            result.append({"p": "|", "r": "\r", "n": "\n", "\\": "\\"}.get(char, char))
            escaped = False
        elif char == "\\":
            escaped = True
        else:
            result.append(char)
    if escaped:
        result.append("\\")
    return "".join(result)


def _to_int(value: str) -> int | None:
    try:
        return int(value)
    except ValueError:
        return None


def capture_tflex_state(timeout_sec: int = 60) -> dict[str, Any]:
    result = run_csharp_snippet(CAPTURE_STATE_CODE, mode="run", timeout_sec=timeout_sec, artifact_prefix="capture_tflex_state")
    state: dict[str, Any] = {
        "ok": result.get("ok") is True,
        "run": result,
        "session_initialized": None,
        "active_document": None,
        "document_count": None,
        "documents": [],
        "object_counts": {"documents": 0, "2d": 0, "3d_operations": 0, "variables": 0},
        "selection": [],
        "artifacts": result.get("artifacts") or [],
        "object2d_types": {},
        "operation3d_types": {},
        "operations3d": [],
        "errors": [],
    }
    for line in (result.get("stdout") or "").splitlines():
        if line.startswith("init="):
            state["session_initialized"] = _parse_bool(line.split("=", 1)[1])
        elif line.startswith("activeNull="):
            active_null = _parse_bool(line.split("=", 1)[1])
            if active_null is True:
                state["active_document"] = None
        elif line.startswith("active="):
            title, _, file_name = line.split("=", 1)[1].partition("|")
            state["active_document"] = {"title": _decode(title), "file_name": _decode(file_name)}
        elif line.startswith("doc="):
            parts = line.split("=", 1)[1].split("|")
            if len(parts) >= 7:
                doc = {
                    "index": _to_int(parts[0]),
                    "title": _decode(parts[1]),
                    "file_name": _decode(parts[2]),
                    "file_path": _decode(parts[3]),
                    "changed": _parse_bool(parts[7]) if len(parts) > 7 else None,
                    "object_counts": {
                        "2d": _to_int(parts[4]),
                        "3d_operations": _to_int(parts[5]),
                        "variables": _to_int(parts[6]),
                    },
                }
                state["documents"].append(doc)
        elif line.startswith("documents="):
            try:
                state["document_count"] = int(line.split("=", 1)[1])
            except ValueError:
                pass
        elif line.startswith("object2dType="):
            parts = line.split("=", 1)[1].split("|")
            if len(parts) == 3:
                state["object2d_types"][parts[1]] = (state["object2d_types"].get(parts[1], 0) or 0) + (_to_int(parts[2]) or 0)
        elif line.startswith("operation3dType="):
            parts = line.split("=", 1)[1].split("|")
            if len(parts) == 3:
                state["operation3d_types"][parts[1]] = (state["operation3d_types"].get(parts[1], 0) or 0) + (_to_int(parts[2]) or 0)
        elif line.startswith("operation3d="):
            parts = line.split("=", 1)[1].split("|")
            if len(parts) >= 7:
                state["operations3d"].append({
                    "document_index": _to_int(parts[0]),
                    "operation_index": _to_int(parts[1]),
                    "type": parts[2],
                    "bbox_valid": _parse_bool(parts[3]),
                    "bbox_min": parts[4],
                    "bbox_max": parts[5],
                    "bbox_size": parts[6],
                    "error": _decode(parts[7]) if len(parts) > 7 and parts[7] else None,
                })
        elif line.startswith("object2dError=") or line.startswith("operation3dError="):
            state["errors"].append(line)
    if state["document_count"] is None:
        state["document_count"] = len(state["documents"])
    state["object_counts"]["documents"] = state["document_count"]
    for doc in state["documents"]:
        counts = doc.get("object_counts") or {}
        for key in ["2d", "3d_operations", "variables"]:
            value = counts.get(key)
            if isinstance(value, int) and value > 0:
                state["object_counts"][key] += value
    return state
