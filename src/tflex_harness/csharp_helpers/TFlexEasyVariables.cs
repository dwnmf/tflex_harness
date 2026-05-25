using System;
using TFlex.Model;

namespace TFlexEasy {
  public static class EasyVariables {
    public static Variable Find(Document doc, string name) {
      if (doc == null) throw new ArgumentNullException("doc");
      foreach (Variable variable in doc.GetVariables()) {
        if (variable.Name == name) return variable;
      }
      return null;
    }

    public static bool Exists(Document doc, string name) {
      return Find(doc, name) != null;
    }

    public static string TextValue(Document doc, string name) {
      Variable variable = Find(doc, name);
      if (variable == null) return null;
      return variable.TextValue;
    }

    public static double RealValue(Document doc, string name) {
      Variable variable = Find(doc, name);
      if (variable == null) throw new InvalidOperationException("Variable not found: " + name);
      return variable.RealValue;
    }

    public static bool SetTextConstant(Document doc, string name, string value) {
      Variable variable = Find(doc, name);
      if (variable == null) {
        EasyDiagnostics.Print("variable.missing", name);
        return false;
      }
      if (!variable.IsText) {
        EasyDiagnostics.Print("variable.notText", name);
        return false;
      }
      EasyDiagnostics.Print("variable.before." + name, variable.TextValue);
      string expression = TextExpression(value);
      variable.Expression = expression;
      EasyDiagnostics.Print("variable.after." + name, variable.TextValue);
      EasyDiagnostics.Print("variable.expression." + name, variable.Expression);
      return variable.Expression == expression;
    }

    public static bool SetRealConstant(Document doc, string name, double value) {
      Variable variable = Find(doc, name);
      if (variable == null) {
        EasyDiagnostics.Print("variable.missing", name);
        return false;
      }
      if (!variable.IsReal) {
        EasyDiagnostics.Print("variable.notReal", name);
        return false;
      }
      EasyDiagnostics.Print("variable.before." + name, variable.RealValue);
      variable.RealValue = value;
      EasyDiagnostics.Print("variable.after." + name, variable.RealValue);
      EasyDiagnostics.Print("variable.expression." + name, variable.Expression);
      return Math.Abs(variable.RealValue - value) < 1e-9;
    }

    public static string TextExpression(string value) {
      if (value == null) value = "";
      return "\"" + value.Replace("\\", "\\\\").Replace("\"", "\\\"") + "\"";
    }
  }
}
