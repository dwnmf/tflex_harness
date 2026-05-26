using System;
using System.Collections;
using System.Collections.Generic;
using System.Reflection;
using TFlex.Model;
using TFlex.Model.Model2D;
using TFlexEasy;

public class Program {
  public static int Main(){
    string source = Environment.GetEnvironmentVariable("TFLEX_PROTOTYPE_SOURCE_PATH");
    if (String.IsNullOrWhiteSpace(source)) {
      EasyDiagnostics.Print("probe.error", "TFLEX_PROTOTYPE_SOURCE_PATH is required");
      return 2;
    }

    Document doc = null;
    using (var sess = EasySession.Start3D()) {
      string copy = sess.ArtifactPath("electrical_probe_copy.grb");
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
    EasyDiagnostics.Print("probe.kind", "electrical_objects");
    ProbeDocumentVariables(doc);
    Probe2DObjects(doc);
    ProbeAllModelObjects(doc);
  }

  static void ProbeDocumentVariables(Document doc) {
    int count = 0;
    foreach (Variable variable in doc.GetVariables()) {
      if (count < 80) {
        SafePrint("variable." + count + ".name", variable.Name);
        SafePrint("variable." + count + ".isText", variable.IsText);
        SafePrint("variable." + count + ".isReal", variable.IsReal);
        if (variable.IsText) SafePrint("variable." + count + ".text", Shorten(variable.TextValue, 180));
        if (variable.IsReal) SafePrint("variable." + count + ".real", variable.RealValue);
        SafePrint("variable." + count + ".expression", Shorten(variable.Expression, 180));
      }
      count++;
    }
    SafePrint("variable.count", count);
  }

  static void Probe2DObjects(Document doc) {
    Dictionary<string, int> hist = new Dictionary<string, int>();
    int index = 0;
    int fragmentCount = 0;
    int connectorCount = 0;
    foreach (Object2D obj in doc.Get2DObjects()) {
      Count(hist, obj.GetType().FullName);
      if (index < 120) {
        SafePrint("object2d." + index + ".type", obj.GetType().FullName);
        PrintReflectedMembers("object2d." + index, obj, 24);
      }
      LineText line = obj as LineText;
      if (line != null && !String.IsNullOrWhiteSpace(line.TextValue)) SafePrint("object2d." + index + ".lineText", Shorten(line.TextValue, 240));
      RichText rich = obj as RichText;
      if (rich != null) ProbeRichText("object2d." + index + ".rich", rich);
      Fragment fragment = obj as Fragment;
      if (fragment != null) {
        ProbeFragment("fragment." + fragmentCount, fragment);
        fragmentCount++;
      }
      Connector connector = obj as Connector;
      if (connector != null) {
        ProbeConnector("connector." + connectorCount, connector);
        connectorCount++;
      }
      index++;
    }
    SafePrint("object2d.count", index);
    SafePrint("fragment.count", fragmentCount);
    SafePrint("connector.count", connectorCount);
    PrintHistogram("object2d.type", hist);
  }

  static void ProbeAllModelObjects(Document doc) {
    object all = SafeInvoke(doc, "GetObjects");
    IEnumerable enumerable = all as IEnumerable;
    if (enumerable == null) {
      SafePrint("modelObjects.available", false);
      return;
    }
    Dictionary<string, int> hist = new Dictionary<string, int>();
    int index = 0;
    foreach (object obj in enumerable) {
      if (obj == null) continue;
      string typeName = obj.GetType().FullName;
      Count(hist, typeName);
      bool interestingType = Interesting(typeName) || typeName.IndexOf("Circuits", StringComparison.OrdinalIgnoreCase) >= 0;
      if (interestingType && index < 160) {
        SafePrint("modelObject." + index + ".type", typeName);
        PrintReflectedMembers("modelObject." + index, obj, 24);
        ProbeConnectorParameters("modelObject." + index, obj);
      }
      index++;
    }
    SafePrint("modelObject.count", index);
    PrintHistogram("modelObject.type", hist);
  }

  static void ProbeFragment(string prefix, Fragment fragment) {
    try {
      SafePrint(prefix + ".displayName", fragment.DisplayName);
      SafePrint(prefix + ".name", fragment.Name);
      SafePrint(prefix + ".fileName", SafeStringProperty(fragment, "FileName"));
      SafePrint(prefix + ".filePath", SafeStringProperty(fragment, "FilePath"));
      PrintReflectedMembers(prefix, fragment, 40);
      ProbeConnectorParameters(prefix + ".connector", SafeProperty(fragment, "Connector"));
      ProbeVariables(prefix + ".var", SafeInvoke(fragment, "GetVariables"), 80);
      MethodInfo mi = fragment.GetType().GetMethod("GetVariables", new Type[] { typeof(bool) });
      if (mi != null) ProbeVariables(prefix + ".varInternal", mi.Invoke(fragment, new object[] { true }), 120);
    } catch (Exception ex) {
      SafePrint(prefix + ".error", ex.GetType().Name + ": " + ex.Message);
    }
  }

  static void ProbeConnector(string prefix, Connector connector) {
    try {
      SafePrint(prefix + ".displayName", connector.DisplayName);
      SafePrint(prefix + ".name", connector.Name);
      PrintReflectedMembers(prefix, connector, 40);
      ProbeConnectorParameters(prefix + ".parameters", SafeProperty(connector, "Parameters"));
    } catch (Exception ex) {
      SafePrint(prefix + ".error", ex.GetType().Name + ": " + ex.Message);
    }
  }

  static void ProbeVariables(string prefix, object variables, int max) {
    IEnumerable enumerable = variables as IEnumerable;
    if (enumerable == null) {
      SafePrint(prefix + ".null", variables == null);
      if (variables != null) SafePrint(prefix + ".type", variables.GetType().FullName);
      return;
    }
    int index = 0;
    foreach (object item in enumerable) {
      if (item == null) continue;
      SafePrint(prefix + "." + index + ".type", item.GetType().FullName);
      PrintReflectedMembers(prefix + "." + index, item, 24);
      index++;
      if (index >= max) break;
    }
    SafePrint(prefix + ".countSample", index);
  }

  static void ProbeConnectorParameters(string prefix, object parameters) {
    if (parameters == null) return;
    string typeName = parameters.GetType().FullName;
    if (typeName == null || typeName.IndexOf("Connector", StringComparison.OrdinalIgnoreCase) < 0) return;
    SafePrint(prefix + ".type", typeName);
    PrintReflectedMembers(prefix, parameters, 24);
    for (int i = 0; i < 40; i++) {
      try {
        object name = SafeInvoke(parameters, "GetParameter", new object[] { i });
        if (name == null) break;
        string n = Convert.ToString(name);
        SafePrint(prefix + ".param." + i + ".name", n);
        object isText = SafeInvoke(parameters, "IsText", new object[] { i });
        object isReal = SafeInvoke(parameters, "IsReal", new object[] { i });
        SafePrint(prefix + ".param." + i + ".isText", isText);
        SafePrint(prefix + ".param." + i + ".isReal", isReal);
        if (Convert.ToString(isText) == "True") SafePrint(prefix + ".param." + i + ".text", Shorten(Convert.ToString(SafeInvoke(parameters, "GetTextValue", new object[] { i })), 180));
        if (Convert.ToString(isReal) == "True") SafePrint(prefix + ".param." + i + ".real", SafeInvoke(parameters, "GetRealValue", new object[] { i }));
      } catch (Exception ex) {
        SafePrint(prefix + ".param." + i + ".error", ex.GetType().Name + ": " + ex.Message);
        break;
      }
    }
  }

  static void ProbeRichText(string prefix, RichText rich) {
    bool editing = false;
    try {
      rich.BeginEdit();
      editing = true;
      SafePrint(prefix + ".tableOnly", rich.TableOnly);
      if (!rich.TableOnly) SafePrint(prefix + ".text", Shorten(rich.TextValue, 240));
    } catch (Exception ex) {
      SafePrint(prefix + ".error", ex.GetType().Name + ": " + ex.Message);
    } finally {
      if (editing) { try { rich.EndEdit(); } catch {} }
    }
  }

  static void PrintReflectedMembers(string prefix, object obj, int max) {
    if (obj == null) return;
    Type t = obj.GetType();
    PropertyInfo[] props = t.GetProperties(BindingFlags.Public | BindingFlags.Instance);
    Array.Sort(props, delegate(PropertyInfo a, PropertyInfo b) { return String.CompareOrdinal(a.Name, b.Name); });
    int printed = 0;
    for (int i = 0; i < props.Length; i++) {
      PropertyInfo pi = props[i];
      if (pi.GetIndexParameters().Length != 0) continue;
      if (!Interesting(pi.Name) && !Interesting(pi.PropertyType.FullName)) continue;
      SafePrint(prefix + ".member." + pi.Name, pi.PropertyType.FullName + " read=" + pi.CanRead + " write=" + pi.CanWrite);
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

  static object SafeProperty(object obj, string name) {
    if (obj == null) return null;
    try {
      PropertyInfo pi = obj.GetType().GetProperty(name);
      if (pi == null || !pi.CanRead || pi.GetIndexParameters().Length != 0) return null;
      return pi.GetValue(obj, null);
    } catch { return null; }
  }

  static string SafeStringProperty(object obj, string name) {
    object value = SafeProperty(obj, name);
    return value == null ? "<null>" : Shorten(Convert.ToString(value), 240);
  }

  static object SafeInvoke(object obj, string methodName) {
    return SafeInvoke(obj, methodName, null);
  }

  static object SafeInvoke(object obj, string methodName, object[] args) {
    if (obj == null) return null;
    try {
      MethodInfo mi = null;
      MethodInfo[] methods = obj.GetType().GetMethods(BindingFlags.Public | BindingFlags.Instance | BindingFlags.Static);
      for (int i = 0; i < methods.Length; i++) {
        if (methods[i].Name != methodName) continue;
        if ((args == null && methods[i].GetParameters().Length == 0) || (args != null && methods[i].GetParameters().Length == args.Length)) { mi = methods[i]; break; }
      }
      if (mi == null) return null;
      return mi.Invoke(obj, args);
    } catch (TargetInvocationException ex) {
      SafePrint("invoke." + methodName + ".error", ex.InnerException == null ? ex.Message : ex.InnerException.GetType().Name + ": " + ex.InnerException.Message);
      return null;
    } catch (Exception ex) {
      SafePrint("invoke." + methodName + ".error", ex.GetType().Name + ": " + ex.Message);
      return null;
    }
  }

  static void Count(Dictionary<string, int> hist, string key) {
    if (!hist.ContainsKey(key)) hist[key] = 0;
    hist[key]++;
  }

  static void PrintHistogram(string prefix, Dictionary<string, int> hist) {
    int h = 0;
    foreach (KeyValuePair<string, int> kv in hist) {
      SafePrint(prefix + "." + h, kv.Key + "=" + kv.Value);
      h++;
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
    return v.IndexOf("text") >= 0 || v.IndexOf("name") >= 0 || v.IndexOf("value") >= 0 ||
      v.IndexOf("mark") >= 0 || v.IndexOf("label") >= 0 || v.IndexOf("reference") >= 0 ||
      v.IndexOf("variable") >= 0 || v.IndexOf("connector") >= 0 || v.IndexOf("contact") >= 0 ||
      v.IndexOf("circuit") >= 0 || v.IndexOf("link") >= 0 || v.IndexOf("fragment") >= 0 ||
      v.IndexOf("id") >= 0 || v.IndexOf("data") >= 0 || v.IndexOf("symbol") >= 0;
  }

  static bool IsSimple(Type type) {
    return type.IsPrimitive || type.IsEnum || type == typeof(string) || type == typeof(Guid) || type == typeof(decimal);
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
