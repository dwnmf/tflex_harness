using System;
using System.Collections;
using System.Collections.Generic;
using System.Reflection;
using TFlex.Model;
using TFlex.Model.Model2D;
using TFlexEasy;
using BOMObject = TFlex.Model.Model2D.BOMObject;

public class Program {
  public static int Main(){
    string source = Environment.GetEnvironmentVariable("TFLEX_PROTOTYPE_SOURCE_PATH");
    if (String.IsNullOrWhiteSpace(source)) {
      EasyDiagnostics.Print("probe.error", "TFLEX_PROTOTYPE_SOURCE_PATH is required");
      return 2;
    }

    Document doc = null;
    using (var sess = EasySession.Start3D()) {
      string copy = sess.ArtifactPath("specification_probe_copy.grb");
      try {
        EasyPrototype.CopyToArtifact(source, copy);
        doc = EasyPrototype.OpenCopy(copy, visible: false);
        ProbeDocument(doc);
        return 0;
      } catch (Exception ex) {
        EasyDiagnostics.Print("probe.exception", ex.GetType().FullName + ": " + ex.Message);
        EasyDiagnostics.Print("probe.stack", Shorten(ex.ToString(), 900));
        return 20;
      } finally {
        EasyPrototype.Close(doc);
      }
    }
  }

  static void ProbeDocument(Document doc) {
    EasyDiagnostics.Print("probe.kind", "specification_objects");
    ProbeVariables(doc);
    Probe2DObjects(doc);
    ProbeProductStructure(doc);
  }

  static void ProbeVariables(Document doc) {
    int count = 0;
    foreach (Variable variable in doc.GetVariables()) {
      if (count < 40) {
        SafePrint("variable." + count + ".name", variable.Name);
        SafePrint("variable." + count + ".isText", variable.IsText);
        SafePrint("variable." + count + ".isReal", variable.IsReal);
        if (variable.IsText) SafePrint("variable." + count + ".text", Shorten(variable.TextValue, 160));
        SafePrint("variable." + count + ".expression", Shorten(variable.Expression, 160));
      }
      count++;
    }
    EasyDiagnostics.Print("variable.count", count);
  }

  static void Probe2DObjects(Document doc) {
    Dictionary<string, int> hist = new Dictionary<string, int>();
    int index = 0;
    int richCount = 0;
    int bomCount = 0;
    foreach (Object2D obj in doc.Get2DObjects()) {
      string typeName = obj.GetType().FullName;
      if (!hist.ContainsKey(typeName)) hist[typeName] = 0;
      hist[typeName]++;
      if (index < 80) {
        SafePrint("object." + index + ".type", typeName);
        PrintReflectedMembers("object." + index, obj, 16);
      }
      RichText rich = obj as RichText;
      if (rich != null) {
        ProbeRichText("richText." + richCount, rich);
        richCount++;
      }
      BOMObject bom = obj as BOMObject;
      if (bom != null) {
        ProbeBomObject("bom." + bomCount, bom);
        bomCount++;
      }
      index++;
    }
    EasyDiagnostics.Print("object.count", index);
    EasyDiagnostics.Print("richText.count", richCount);
    EasyDiagnostics.Print("bom.count", bomCount);
    int h = 0;
    foreach (KeyValuePair<string, int> kv in hist) {
      SafePrint("object.type." + h, kv.Key + "=" + kv.Value);
      h++;
    }
  }

  static void ProbeRichText(string prefix, RichText rich) {
    bool editing = false;
    try {
      rich.BeginEdit();
      editing = true;
      SafePrint(prefix + ".tableOnly", rich.TableOnly);
      if (!rich.TableOnly) SafePrint(prefix + ".text", Shorten(rich.TextValue, 220));
      for (int tableIndex = 0; tableIndex < 3; tableIndex++) {
        try {
          Table table = rich.GetTableByIndex((uint)tableIndex);
          SafePrint(prefix + ".table." + tableIndex + ".type", table.GetType().FullName);
          PrintReflectedMembers(prefix + ".table." + tableIndex, table, 20);
          for (uint cell = 0; cell < 12; cell++) {
            try {
              string text = table.GetCellText(cell);
              SafePrint(prefix + ".table." + tableIndex + ".cell." + cell, Shorten(Normalize(text), 120));
            } catch (Exception ex) {
              SafePrint(prefix + ".table." + tableIndex + ".cell." + cell + ".error", ex.GetType().Name + ": " + ex.Message);
              break;
            }
          }
        } catch (Exception ex) {
          SafePrint(prefix + ".table." + tableIndex + ".error", ex.GetType().Name + ": " + ex.Message);
          break;
        }
      }
    } catch (Exception ex) {
      SafePrint(prefix + ".error", ex.GetType().Name + ": " + ex.Message);
    } finally {
      if (editing) {
        try { rich.EndEdit(); } catch (Exception ex) { SafePrint(prefix + ".endEdit.error", ex.GetType().Name + ": " + ex.Message); }
      }
    }
  }

  static void ProbeBomObject(string prefix, BOMObject bom) {
    bool editing = false;
    try {
      SafePrint(prefix + ".friendlyName", bom.FriendlyName);
      SafePrint(prefix + ".subType", bom.SubType);
      SafePrint(prefix + ".reportID", bom.ReportID);
      PrintReflectedMembers(prefix, bom, 32);
      bom.BeginEdit();
      editing = true;
      try { bom.MoveToFrontRecord(); SafePrint(prefix + ".moveToFront", true); }
      catch (Exception ex) { SafePrint(prefix + ".moveToFront.error", ex.GetType().Name + ": " + ex.Message); }
      SafePrint(prefix + ".recordID", bom.RecordID);
      SafePrint(prefix + ".recordGroup", bom.RecordGroup);
      SafePrint(prefix + ".recordGroupFullName", bom.RecordGroupFullName);
      SafePrint(prefix + ".recordPosition", bom.RecordPosition);
      SafePrint(prefix + ".recordFlags", bom.RecordFlags);
      ProbeStringArray(prefix + ".visibleField", SafeInvokeArray(bom, "GetVisibleFields"), 40);
      ProbeStringArray(prefix + ".allField", SafeInvokeArray(bom, "GetAllFields"), 80);
      int sfIndex = 0;
      foreach (object value in Enum.GetValues(typeof(BOMObject.StandardField))) {
        BOMObject.StandardField field = (BOMObject.StandardField)value;
        try {
          string text = bom.GetStandardFieldValue(field);
          if (!String.IsNullOrEmpty(text)) SafePrint(prefix + ".standard." + field.ToString(), Shorten(text, 160));
        } catch (Exception ex) {
          if (sfIndex < 8) SafePrint(prefix + ".standard." + field.ToString() + ".error", ex.GetType().Name + ": " + ex.Message);
        }
        sfIndex++;
      }
    } catch (Exception ex) {
      SafePrint(prefix + ".error", ex.GetType().Name + ": " + ex.Message);
    } finally {
      if (editing) {
        try { bom.EndEdit(); SafePrint(prefix + ".endEdit", true); }
        catch (Exception ex) { SafePrint(prefix + ".endEdit.error", ex.GetType().Name + ": " + ex.Message); }
      }
    }
  }

  static void ProbeProductStructure(Document doc) {
    try {
      ProductStructure ps = ProductStructure.GetActiveProductStructure(doc);
      SafePrint("productStructure.active", ps != null);
      if (ps == null) return;
      SafePrint("productStructure.type", ps.GetType().FullName);
      SafePrint("productStructure.schemeId", ps.SchemeId);
      PrintReflectedMembers("productStructure", ps, 40);
      object scheme = SafeInvoke(ps, "GetScheme");
      if (scheme != null) {
        SafePrint("productStructure.scheme.type", scheme.GetType().FullName);
        PrintReflectedMembers("productStructure.scheme", scheme, 60);
        ProbeEnumerableProperties("productStructure.scheme", scheme, 4, 12);
      }
      object reports = SafeInvoke(ps, "GetExternalReports");
      ProbeEnumerable("productStructure.externalReport", reports as IEnumerable, 8, 8);
      object rows = SafeInvoke(ps, "GetAllRowElements");
      ProbeEnumerable("productStructure.row", rows as IEnumerable, 8, 24);
    } catch (Exception ex) {
      SafePrint("productStructure.error", ex.GetType().Name + ": " + ex.Message);
    }
  }

  static void ProbeEnumerableProperties(string prefix, object obj, int maxProps, int maxItems) {
    int props = 0;
    PropertyInfo[] pis = obj.GetType().GetProperties(BindingFlags.Public | BindingFlags.Instance);
    foreach (PropertyInfo pi in pis) {
      if (!pi.CanRead || pi.GetIndexParameters().Length != 0) continue;
      if (typeof(string).IsAssignableFrom(pi.PropertyType)) continue;
      if (!typeof(IEnumerable).IsAssignableFrom(pi.PropertyType)) continue;
      try {
        object value = pi.GetValue(obj, null);
        ProbeEnumerable(prefix + "." + pi.Name, value as IEnumerable, maxItems, 16);
        props++;
        if (props >= maxProps) break;
      } catch (Exception ex) {
        SafePrint(prefix + "." + pi.Name + ".error", ex.GetType().Name + ": " + ex.Message);
      }
    }
  }

  static void ProbeEnumerable(string prefix, IEnumerable items, int maxItems, int maxMembers) {
    if (items == null) { SafePrint(prefix + ".null", true); return; }
    int index = 0;
    foreach (object item in items) {
      if (item == null) {
        SafePrint(prefix + "." + index + ".null", true);
      } else {
        SafePrint(prefix + "." + index + ".type", item.GetType().FullName);
        PrintReflectedMembers(prefix + "." + index, item, maxMembers);
        ProbeRowCells(prefix + "." + index, item);
      }
      index++;
      if (index >= maxItems) break;
    }
    SafePrint(prefix + ".sampleCount", index);
  }

  static void ProbeRowCells(string prefix, object item) {
    if (item == null || item.GetType().FullName != "TFlex.Model.RowElement") return;
    string[] propertyNames = new string[] { "IncludeInDoc", "IncludeInAssembly", "Position" };
    for (int i = 0; i < propertyNames.Length; i++) {
      try {
        PropertyInfo pi = item.GetType().GetProperty(propertyNames[i]);
        if (pi == null) continue;
        object cell = pi.GetValue(item, null);
        if (cell == null) continue;
        SafePrint(prefix + ".cell." + propertyNames[i] + ".type", cell.GetType().FullName);
        PrintReflectedMembers(prefix + ".cell." + propertyNames[i], cell, 12);
      } catch (Exception ex) {
        SafePrint(prefix + ".cell." + propertyNames[i] + ".error", ex.GetType().Name + ": " + ex.Message);
      }
    }
  }

  static Array SafeInvokeArray(object obj, string methodName) {
    object value = SafeInvoke(obj, methodName);
    return value as Array;
  }

  static object SafeInvoke(object obj, string methodName) {
    if (obj == null) return null;
    try {
      MethodInfo mi = obj.GetType().GetMethod(methodName, new Type[0]);
      if (mi == null) return null;
      return mi.Invoke(obj, null);
    } catch (TargetInvocationException ex) {
      SafePrint("invoke." + methodName + ".error", ex.InnerException == null ? ex.Message : ex.InnerException.GetType().Name + ": " + ex.InnerException.Message);
      return null;
    } catch (Exception ex) {
      SafePrint("invoke." + methodName + ".error", ex.GetType().Name + ": " + ex.Message);
      return null;
    }
  }

  static void ProbeStringArray(string prefix, Array values, int max) {
    if (values == null) { SafePrint(prefix + ".null", true); return; }
    int limit = Math.Min(values.Length, max);
    for (int i = 0; i < limit; i++) SafePrint(prefix + "." + i, Shorten(Convert.ToString(values.GetValue(i)), 160));
    SafePrint(prefix + ".count", values.Length);
  }

  static void PrintReflectedMembers(string prefix, object obj, int max) {
    if (obj == null) return;
    Type t = obj.GetType();
    int printed = 0;
    PropertyInfo[] props = t.GetProperties(BindingFlags.Public | BindingFlags.Instance);
    Array.Sort(props, delegate(PropertyInfo a, PropertyInfo b) { return String.CompareOrdinal(a.Name, b.Name); });
    for (int i = 0; i < props.Length; i++) {
      PropertyInfo pi = props[i];
      if (pi.GetIndexParameters().Length != 0) continue;
      if (!Interesting(pi.Name) && !Interesting(pi.PropertyType.FullName)) continue;
      string info = pi.PropertyType.FullName + " read=" + pi.CanRead + " write=" + pi.CanWrite;
      SafePrint(prefix + ".member." + pi.Name, info);
      if (pi.CanRead && IsSimple(pi.PropertyType)) {
        try { SafePrint(prefix + ".value." + pi.Name, Shorten(Convert.ToString(pi.GetValue(obj, null)), 220)); }
        catch (Exception ex) { SafePrint(prefix + ".value." + pi.Name + ".error", ex.GetType().Name + ": " + ex.Message); }
      }
      printed++;
      if (printed >= max) break;
    }
    MethodInfo[] methods = t.GetMethods(BindingFlags.Public | BindingFlags.Instance | BindingFlags.Static);
    Array.Sort(methods, delegate(MethodInfo a, MethodInfo b) { return String.CompareOrdinal(a.Name, b.Name); });
    int methodPrinted = 0;
    for (int i = 0; i < methods.Length; i++) {
      MethodInfo mi = methods[i];
      if (mi.IsSpecialName) continue;
      if (!Interesting(mi.Name)) continue;
      SafePrint(prefix + ".method." + methodPrinted, MethodSignature(mi));
      methodPrinted++;
      if (methodPrinted >= max) break;
    }
  }

  static string MethodSignature(MethodInfo mi) {
    ParameterInfo[] ps = mi.GetParameters();
    string[] parts = new string[ps.Length];
    for (int i = 0; i < ps.Length; i++) parts[i] = ps[i].ParameterType.FullName + " " + ps[i].Name;
    return mi.ReturnType.FullName + " " + mi.Name + "(" + String.Join(",", parts) + ")";
  }

  static bool Interesting(string s) {
    if (String.IsNullOrEmpty(s)) return false;
    string v = s.ToLowerInvariant();
    return v.IndexOf("spec") >= 0 || v.IndexOf("bom") >= 0 || v.IndexOf("table") >= 0 ||
      v.IndexOf("cell") >= 0 || v.IndexOf("row") >= 0 || v.IndexOf("text") >= 0 ||
      v.IndexOf("value") >= 0 || v.IndexOf("data") >= 0 || v.IndexOf("field") >= 0 ||
      v.IndexOf("report") >= 0 || v.IndexOf("name") >= 0 || v.IndexOf("id") >= 0;
  }

  static bool IsSimple(Type type) {
    return type.IsPrimitive || type.IsEnum || type == typeof(string) || type == typeof(Guid) || type == typeof(decimal);
  }

  static string Normalize(string value) {
    if (value == null) return "";
    return value.Replace("\r\n", "\n").TrimEnd('\r', '\n');
  }

  static string Shorten(string value, int max) {
    if (value == null) return "<null>";
    value = value.Replace("\r", "\\r").Replace("\n", "\\n");
    if (value.Length <= max) return value;
    return value.Substring(0, max) + "...";
  }

  static void SafePrint(string key, object value) {
    try { EasyDiagnostics.Print(key, value); } catch { Console.WriteLine(key + "=" + Convert.ToString(value)); }
  }
}

