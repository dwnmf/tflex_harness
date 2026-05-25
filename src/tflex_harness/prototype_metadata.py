from __future__ import annotations

import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

from .artifacts import ArtifactStore, json_default, slugify
from .prototypes import scan_prototypes
from .runner import run_csharp_snippet


PROTOTYPE_METADATA_CODE = r'''
using System;
using System.Collections;
using System.Collections.Generic;
using System.Globalization;
using System.Reflection;
using System.Text;
using TFlex;
using TFlex.Model;
using TFlex.Model.Model2D;
using TFlex.Model.Model3D;
using TFlexEasy;

public class Program {
  public static int Main(){
    Console.OutputEncoding = Encoding.UTF8;
    string source = Environment.GetEnvironmentVariable("TFLEX_PROTOTYPE_SOURCE_PATH");
    if (String.IsNullOrWhiteSpace(source)) {
      EasyDiagnostics.Print("metadata.error", "TFLEX_PROTOTYPE_SOURCE_PATH is required");
      return 2;
    }

    Document doc = null;
    using (var sess = EasySession.Start3D()) {
      string copy = sess.ArtifactPath("prototype_metadata_copy.grb");
      try {
        EasyPrototype.CopyToArtifact(source, copy);
        doc = EasyPrototype.OpenCopy(copy, visible: false);
        WriteDocument(doc);
        return 0;
      } finally {
        EasyPrototype.Close(doc);
      }
    }
  }

  static void WriteDocument(Document doc) {
    Console.WriteLine("document.title=" + Encode(doc.Title));
    Console.WriteLine("document.fileName=" + Encode(doc.FileName));
    Console.WriteLine("document.filePath=" + Encode(doc.FilePath));
    Console.WriteLine("document.changed=" + doc.Changed);
    Count2D(doc);
    Count3DOperations(doc);
    WriteVariables(doc);
    WriteReflectedCount(doc, "pages", new string[] {"Pages", "GetPages"});
    WriteReflectedCount(doc, "fragments", new string[] {"Fragments", "GetFragments"});
  }

  static void Count2D(Document doc) {
    try {
      Dictionary<string, int> types = new Dictionary<string, int>();
      int count = 0;
      int textLike = 0;
      int tableLike = 0;
      foreach (Object2D obj in doc.Get2DObjects()) {
        count++;
        string type = obj.GetType().FullName;
        if (!types.ContainsKey(type)) types[type] = 0;
        types[type]++;
        if (type.IndexOf("Text", StringComparison.OrdinalIgnoreCase) >= 0) textLike++;
        if (type.IndexOf("Table", StringComparison.OrdinalIgnoreCase) >= 0 || type.IndexOf("Specification", StringComparison.OrdinalIgnoreCase) >= 0) tableLike++;
      }
      Console.WriteLine("count.2d=" + count);
      Console.WriteLine("count.2dTextLike=" + textLike);
      Console.WriteLine("count.2dTableLike=" + tableLike);
      foreach (KeyValuePair<string, int> item in types) Console.WriteLine("object2dType=" + Encode(item.Key) + "|" + item.Value);
    } catch (Exception ex) {
      Console.WriteLine("error.2d=" + Encode(ex.GetType().FullName) + "|" + Encode(ex.Message));
      Console.WriteLine("count.2d=-1");
    }
  }

  static void Count3DOperations(Document doc) {
    try {
      ICollection<Operation> operations = Document3D.GetOperations(doc);
      Dictionary<string, int> types = new Dictionary<string, int>();
      int count = 0;
      int bboxValid = 0;
      foreach (Operation op in operations) {
        count++;
        string type = op.GetType().FullName;
        if (!types.ContainsKey(type)) types[type] = 0;
        types[type]++;
        try {
          if (op.Geometry != null && op.Geometry.AABoundBox != null && op.Geometry.AABoundBox.Valid) bboxValid++;
        } catch {}
      }
      Console.WriteLine("count.3dOperations=" + count);
      Console.WriteLine("count.3dBboxValid=" + bboxValid);
      foreach (KeyValuePair<string, int> item in types) Console.WriteLine("operation3dType=" + Encode(item.Key) + "|" + item.Value);
    } catch (Exception ex) {
      Console.WriteLine("error.3d=" + Encode(ex.GetType().FullName) + "|" + Encode(ex.Message));
      Console.WriteLine("count.3dOperations=-1");
    }
  }

  static void WriteVariables(Document doc) {
    try {
      MethodInfo method = doc.GetType().GetMethod("GetVariables", Type.EmptyTypes);
      if (method == null) {
        Console.WriteLine("count.variables=-1");
        Console.WriteLine("error.variables=missing GetVariables");
        return;
      }
      object variables = method.Invoke(doc, null);
      IEnumerable enumerable = variables as IEnumerable;
      if (enumerable == null) {
        Console.WriteLine("count.variables=-1");
        Console.WriteLine("error.variables=GetVariables returned non-enumerable");
        return;
      }
      int count = 0;
      foreach (object variable in enumerable) {
        Console.WriteLine(
          "variable=" + count + "|" +
          Encode(GetPropertyString(variable, "Name")) + "|" +
          Encode(GetPropertyString(variable, "IsReal")) + "|" +
          Encode(GetPropertyString(variable, "IsText")) + "|" +
          Encode(GetPropertyString(variable, "RealValue")) + "|" +
          Encode(GetPropertyString(variable, "TextValue")) + "|" +
          Encode(GetPropertyString(variable, "Expression")) + "|" +
          Encode(GetPropertyString(variable, "Comment")) + "|" +
          Encode(GetPropertyString(variable, "Hidden")) + "|" +
          Encode(GetPropertyString(variable, "External")) + "|" +
          Encode(GetPropertyString(variable, "ErrorState"))
        );
        count++;
      }
      Console.WriteLine("count.variables=" + count);
    } catch (Exception ex) {
      Console.WriteLine("count.variables=-1");
      Console.WriteLine("error.variables=" + Encode(ex.GetType().FullName) + "|" + Encode(ex.Message));
    }
  }

  static void WriteReflectedCount(object obj, string label, string[] memberNames) {
    foreach (string memberName in memberNames) {
      try {
        object value = null;
        PropertyInfo property = obj.GetType().GetProperty(memberName);
        if (property != null) value = property.GetValue(obj, null);
        if (value == null) {
          MethodInfo method = obj.GetType().GetMethod(memberName, Type.EmptyTypes);
          if (method != null) value = method.Invoke(obj, null);
        }
        if (value == null) continue;
        int count = CountObject(value);
        Console.WriteLine("count." + label + "=" + count);
        Console.WriteLine("metadata." + label + "Source=" + memberName);
        return;
      } catch (Exception ex) {
        Console.WriteLine("error." + label + "=" + memberName + "|" + Encode(ex.GetType().FullName) + "|" + Encode(ex.Message));
      }
    }
    Console.WriteLine("count." + label + "=-1");
  }

  static int CountObject(object value) {
    if (value == null) return -1;
    PropertyInfo countProperty = value.GetType().GetProperty("Count");
    if (countProperty != null) {
      object countValue = countProperty.GetValue(value, null);
      if (countValue is int) return (int)countValue;
    }
    IEnumerable enumerable = value as IEnumerable;
    if (enumerable == null) return -1;
    int count = 0;
    foreach (object item in enumerable) count++;
    return count;
  }

  static string GetPropertyString(object obj, string name) {
    try {
      PropertyInfo property = obj.GetType().GetProperty(name);
      if (property == null) return "";
      object value = property.GetValue(obj, null);
      if (value == null) return "";
      IFormattable formattable = value as IFormattable;
      if (formattable != null) return formattable.ToString(null, CultureInfo.InvariantCulture);
      return value.ToString();
    } catch {
      return "";
    }
  }

  static string Encode(string value) {
    if (value == null) return "";
    return value.Replace("\\", "\\\\").Replace("|", "\\p").Replace("\r", "\\r").Replace("\n", "\\n");
  }
}
'''


MetadataCapture = Callable[[dict[str, Any], int], dict[str, Any]]


def capture_prototype_metadata(prototype: dict[str, Any], timeout_sec: int = 120) -> dict[str, Any]:
    result = run_csharp_snippet(
        PROTOTYPE_METADATA_CODE,
        mode="run",
        timeout_sec=timeout_sec,
        references=["TFlexAPI", "TFlexAPI3D"],
        helpers=["easy_prototype"],
        artifact_prefix="prototype_metadata",
        environment={"TFLEX_PROTOTYPE_SOURCE_PATH": str(prototype["path"])},
    )
    metadata = parse_metadata_stdout(result.get("stdout") or "")
    return {
        "ok": result.get("ok") is True and metadata["document"]["opened"] is True,
        "prototype": prototype,
        "metadata": metadata,
        "run": _run_summary(result),
    }


def capture_metadata_batch(
    root: str | Path | None = None,
    *,
    category: str | None = None,
    limit: int | None = None,
    timeout_sec: int = 120,
    output_dir: str | Path | None = None,
    capture_func: MetadataCapture | None = None,
) -> dict[str, Any]:
    catalog = scan_prototypes(root)
    prototypes = [item for item in catalog["files"] if item["extension"] == ".grb"]
    if category:
        prototypes = [item for item in prototypes if item["category"] == category]
    if limit is not None:
        prototypes = prototypes[:limit]

    out = _output_dir(output_dir)
    metadata_dir = out / "metadata"
    metadata_dir.mkdir(parents=True, exist_ok=True)
    capture = capture_func or capture_prototype_metadata
    rows: list[dict[str, Any]] = []

    for index, prototype in enumerate(prototypes, start=1):
      item = capture(prototype, timeout_sec)
      path = metadata_dir / f"{index:03d}_{slugify(prototype['id'])}.json"
      path.write_text(json.dumps(item, ensure_ascii=False, indent=2, default=json_default) + "\n", encoding="utf-8")
      rows.append(_summary_row(index, prototype, item, path))

    summary = _summary(catalog, prototypes, rows, root=Path(catalog["root"]), category=category)
    index_payload = {
        "ok": summary["failed"] == 0,
        "summary": summary,
        "rows": rows,
    }
    index_path = out / "prototype_metadata_index.json"
    csv_path = out / "prototype_metadata_index.csv"
    index_path.write_text(json.dumps(index_payload, ensure_ascii=False, indent=2, default=json_default) + "\n", encoding="utf-8")
    _write_csv(csv_path, rows)
    index_payload["index_path"] = str(index_path)
    index_payload["csv_path"] = str(csv_path)
    index_payload["metadata_dir"] = str(metadata_dir)
    return index_payload


def parse_metadata_stdout(stdout: str) -> dict[str, Any]:
    metadata: dict[str, Any] = {
        "document": {"opened": False},
        "counts": {},
        "object2d_types": {},
        "operation3d_types": {},
        "variables": [],
        "errors": [],
        "raw_keys": {},
    }
    for line in stdout.splitlines():
        if line.startswith("document.opened="):
            metadata["document"]["opened"] = _parse_bool(line.split("=", 1)[1])
        elif line.startswith("document."):
            key, value = line.split("=", 1)
            metadata["document"][key.removeprefix("document.")] = _decode(value)
        elif line.startswith("count."):
            key, value = line.split("=", 1)
            metadata["counts"][key.removeprefix("count.")] = _to_int(value)
        elif line.startswith("object2dType="):
            type_name, _, count = line.split("=", 1)[1].partition("|")
            metadata["object2d_types"][_decode(type_name)] = _to_int(count)
        elif line.startswith("operation3dType="):
            type_name, _, count = line.split("=", 1)[1].partition("|")
            metadata["operation3d_types"][_decode(type_name)] = _to_int(count)
        elif line.startswith("variable="):
            metadata["variables"].append(_parse_variable(line.split("=", 1)[1]))
        elif line.startswith("error."):
            metadata["errors"].append(line)
        elif "=" in line:
            key, value = line.split("=", 1)
            metadata["raw_keys"][key] = _decode(value)
    return metadata


def _parse_variable(payload: str) -> dict[str, Any]:
    parts = payload.split("|")
    while len(parts) < 11:
        parts.append("")
    return {
        "index": _to_int(parts[0]),
        "name": _decode(parts[1]),
        "is_real": _parse_bool(parts[2]),
        "is_text": _parse_bool(parts[3]),
        "real_value": _decode(parts[4]),
        "text_value": _decode(parts[5]),
        "expression": _decode(parts[6]),
        "comment": _decode(parts[7]),
        "hidden": _parse_bool(parts[8]),
        "external": _parse_bool(parts[9]),
        "error_state": _parse_bool(parts[10]),
    }


def _summary_row(index: int, prototype: dict[str, Any], item: dict[str, Any], path: Path) -> dict[str, Any]:
    metadata = item.get("metadata") or {}
    counts = metadata.get("counts") or {}
    run = item.get("run") or {}
    return {
        "index": index,
        "id": prototype["id"],
        "category": prototype["category"],
        "relative_path": prototype["relative_path"],
        "ok": item.get("ok") is True,
        "run_dir": run.get("run_dir"),
        "metadata_path": str(path),
        "objects2d": counts.get("2d"),
        "text_like_2d": counts.get("2dTextLike"),
        "table_like_2d": counts.get("2dTableLike"),
        "operations3d": counts.get("3dOperations"),
        "variables": counts.get("variables"),
        "pages": counts.get("pages"),
        "fragments": counts.get("fragments"),
        "errors": len(metadata.get("errors") or []),
    }


def _summary(
    catalog: dict[str, Any],
    prototypes: list[dict[str, Any]],
    rows: list[dict[str, Any]],
    *,
    root: Path,
    category: str | None,
) -> dict[str, Any]:
    attempted = len(rows)
    passed = len([row for row in rows if row.get("ok")])
    return {
        "root": str(root),
        "category": category,
        "catalog_grb_count": catalog["grb_count"],
        "selected": len(prototypes),
        "attempted": attempted,
        "passed": passed,
        "failed": attempted - passed,
    }


def _output_dir(output_dir: str | Path | None) -> Path:
    if output_dir is not None:
        out = Path(output_dir)
    else:
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        out = ArtifactStore().root / "prototype_metadata" / stamp
    out.mkdir(parents=True, exist_ok=True)
    return out


def _run_summary(result: dict[str, Any]) -> dict[str, Any]:
    return {
        "ok": result.get("ok"),
        "stage": result.get("stage"),
        "phase": result.get("phase"),
        "exit_code": result.get("exit_code"),
        "run_dir": result.get("run_dir"),
        "stdout_path": result.get("stdout_path"),
        "stderr_path": result.get("stderr_path"),
        "artifacts": result.get("artifacts") or [],
    }


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    fieldnames = [
        "index",
        "id",
        "category",
        "relative_path",
        "ok",
        "objects2d",
        "text_like_2d",
        "table_like_2d",
        "operations3d",
        "variables",
        "pages",
        "fragments",
        "errors",
        "run_dir",
        "metadata_path",
    ]
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def _parse_bool(value: str) -> bool | None:
    if value == "True":
        return True
    if value == "False":
        return False
    return None


def _to_int(value: Any) -> int | None:
    try:
        return int(str(value))
    except (TypeError, ValueError):
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
