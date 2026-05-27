using System;
using TFlex.Model;
using TFlex.Model.Model3D;

namespace TFlexEasy {
  public static class EasyBoolean {
    public static BooleanOperation Unite(Document doc, string name, Operation main, params Operation[] additions) {
      BooleanOperation op = new BooleanOperation(doc);
      op.Name = name;
      op.Function = BooleanOperation.FunctionType.Unite;
      AddFirst(op, main);
      if (additions != null) {
        foreach (Operation addition in additions) AddSecond(op, addition);
      }
      PrintOperands(name, "Unite", main, additions);
      return op;
    }

    public static BooleanOperation Subtract(Document doc, string name, Operation body, params Operation[] cutters) {
      BooleanOperation op = new BooleanOperation(doc);
      op.Name = name;
      op.Function = BooleanOperation.FunctionType.Subtract;
      AddFirst(op, body);
      if (cutters != null) {
        foreach (Operation cutter in cutters) AddSecond(op, cutter);
      }
      PrintOperands(name, "Subtract", body, cutters);
      return op;
    }

    public static BooleanOperation WithBlend(BooleanOperation op, double radiusMm) {
      if (op == null) throw new ArgumentNullException("op");
      op.EdgeFitting = BooleanOperation.FittingType.Blend;
      op.EdgeRadius = new Parameter(radiusMm);
      EasyDiagnostics.Print(op.Name + ".edgeFitting", op.EdgeFitting);
      EasyDiagnostics.Print(op.Name + ".edgeRadiusMm", EasyUnits.F(radiusMm));
      return op;
    }

    public static BooleanOperation WithChamfer(BooleanOperation op, double distanceMm) {
      if (op == null) throw new ArgumentNullException("op");
      op.EdgeFitting = BooleanOperation.FittingType.Chamfer;
      op.EdgeRadius = new Parameter(distanceMm);
      EasyDiagnostics.Print(op.Name + ".edgeFitting", op.EdgeFitting);
      EasyDiagnostics.Print(op.Name + ".edgeRadiusMm", EasyUnits.F(distanceMm));
      return op;
    }

    public static void AddFirst(BooleanOperation op, Operation operand) {
      if (op == null) throw new ArgumentNullException("op");
      if (operand == null) throw new ArgumentNullException("operand");
      op.FirstOperands.Add(new BooleanOperation.OperandsArray.Operand(operand, false));
    }

    public static void AddSecond(BooleanOperation op, Operation operand) {
      if (op == null) throw new ArgumentNullException("op");
      if (operand == null) throw new ArgumentNullException("operand");
      op.SecondOperands.Add(new BooleanOperation.OperandsArray.Operand(operand, false));
    }

    static void PrintOperands(string name, string function, Operation main, Operation[] operands) {
      string label = String.IsNullOrWhiteSpace(name) ? "boolean" : name;
      EasyDiagnostics.Print(label + ".booleanFunction", function);
      EasyDiagnostics.Print(label + ".firstOperand", OperationName(main, "null"));
      EasyDiagnostics.Print(label + ".secondOperandCount", operands == null ? 0 : operands.Length);
      if (operands == null) return;
      for (int i = 0; i < operands.Length; i++) {
        EasyDiagnostics.Print(label + ".secondOperand." + i, OperationName(operands[i], "null"));
      }
    }

    static string OperationName(Operation op, string fallback) {
      if (op == null) return fallback;
      if (String.IsNullOrWhiteSpace(op.Name)) return op.GetType().Name;
      return op.Name;
    }
  }
}
