using System;
using System.Reflection;
using TFlex.Model;

namespace TFlexEasy {
  public static class EasyDocumentProperties {
    public static string Text(Document doc, string name) {
      PropertyInfo property = FindStringProperty(doc, name);
      if (property == null) return null;
      object value = property.GetValue(doc.Properties, null);
      return value == null ? null : value.ToString();
    }

    public static bool SetText(Document doc, string name, string value) {
      if (value == null) value = "";
      PropertyInfo property = FindStringProperty(doc, name);
      if (property == null) {
        EasyDiagnostics.Print("documentProperty.missing", name);
        return false;
      }
      if (!property.CanWrite) {
        EasyDiagnostics.Print("documentProperty.readOnly", name);
        return false;
      }
      EasyDiagnostics.Print("documentProperty.before." + property.Name, Text(doc, property.Name));
      property.SetValue(doc.Properties, value, null);
      EasyDiagnostics.Print("documentProperty.after." + property.Name, Text(doc, property.Name));
      return Text(doc, property.Name) == value;
    }

    public static PropertyInfo FindStringProperty(Document doc, string name) {
      if (doc == null) throw new ArgumentNullException("doc");
      if (String.IsNullOrWhiteSpace(name)) return null;
      Type type = doc.Properties.GetType();
      foreach (PropertyInfo property in type.GetProperties(BindingFlags.Public | BindingFlags.Instance)) {
        if (property.PropertyType != typeof(string)) continue;
        if (String.Equals(property.Name, name, StringComparison.OrdinalIgnoreCase)) return property;
      }
      return null;
    }
  }
}
