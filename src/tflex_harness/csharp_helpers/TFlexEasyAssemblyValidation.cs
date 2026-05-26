using System;
using System.Collections.Generic;
using TFlex.Model;
using TFlex.Model.Model3D;
using TFlex.Model.Model3D.Geometry;

namespace TFlexEasy {
  public sealed class AssemblyBodyRecord {
    public int Index;
    public string Name;
    public Operation Operation;
    public BodyBoxMm Box;
  }

  public sealed class AssemblyValidationReport {
    public int BodyCount;
    public int BBoxOverlapCount;
    public int ClashPairCount;
    public int CollisionCount;
    public int ContactCount;
    public int MateCount;
    public int MateEdgeCount;
    public int MateOperationLinkCount;
    public int MateLinkedFragmentCount;
    public int FragmentCount;
    public int ConnectedFragmentCount;
    public int FloatingFragmentCount;
  }

  public static class EasyAssemblyValidation {
    public static AssemblyValidationReport Validate(Document doc, string label) {
      AssemblyValidationReport report = new AssemblyValidationReport();
      List<AssemblyBodyRecord> bodies = CollectBodies(doc, label);
      report.BodyCount = bodies.Count;
      ValidateBodyClashes(bodies, report, label);
      HashSet<Operation> mateConnectedOperations = ValidateMates(doc, report, label);
      ValidateFragments(doc, report, label, mateConnectedOperations);
      PrintReport(report, label);
      return report;
    }

    public static List<AssemblyBodyRecord> CollectBodies(Document doc, string label) {
      List<AssemblyBodyRecord> bodies = new List<AssemblyBodyRecord>();
      ICollection<Operation> operations = Document3D.GetOperations(doc);
      int index = 0;
      foreach (Operation op in operations) {
        string name = String.IsNullOrWhiteSpace(op.Name) ? op.GetType().Name + "_" + index : op.Name;
        BodyBoxMm box = EasyDiagnostics.GetBodyBoxMm(op);
        bool usable = op.Body != null && op.Geometry != null && box.Valid;
        EasyDiagnostics.Print(label + ".body." + index + ".name", name);
        EasyDiagnostics.Print(label + ".body." + index + ".type", op.GetType().FullName);
        EasyDiagnostics.Print(label + ".body." + index + ".usable", usable);
        if (usable) {
          EasyDiagnostics.PrintBodyBoxMm(label + ".body." + index, op);
          bodies.Add(new AssemblyBodyRecord { Index = index, Name = name, Operation = op, Box = box });
        }
        index++;
      }
      EasyDiagnostics.Print(label + ".operationCount", operations.Count);
      EasyDiagnostics.Print(label + ".bodyCount", bodies.Count);
      return bodies;
    }

    public static void ValidateBodyClashes(List<AssemblyBodyRecord> bodies, AssemblyValidationReport report, string label) {
      for (int i = 0; i < bodies.Count; i++) {
        for (int j = i + 1; j < bodies.Count; j++) {
          AssemblyBodyRecord a = bodies[i];
          AssemblyBodyRecord b = bodies[j];
          bool bboxOverlap = BoxesOverlap(a.Box, b.Box);
          EasyDiagnostics.Print(label + ".pair." + i + "_" + j + ".bboxOverlap", bboxOverlap);
          if (!bboxOverlap) continue;
          report.BBoxOverlapCount++;
          bool pairClashed = false;
          int bodyPairCount = 0;
          try {
            int aCount = a.Operation.Geometry.Solid.Length;
            int bCount = b.Operation.Geometry.Solid.Length;
            EasyDiagnostics.Print(label + ".pair." + i + "_" + j + ".solidCountA", aCount);
            EasyDiagnostics.Print(label + ".pair." + i + "_" + j + ".solidCountB", bCount);
            for (int ai = 0; ai < aCount; ai++) {
              BaseBody bodyA = a.Operation.Geometry.Solid[ai];
              if (bodyA == null) continue;
              for (int bi = 0; bi < bCount; bi++) {
                BaseBody bodyB = b.Operation.Geometry.Solid[bi];
                if (bodyB == null) continue;
                bodyPairCount++;
                ICollection<BaseClashResultItem> clashes = bodyA.Clash(bodyB, false, true);
                report.ClashPairCount++;
                EasyDiagnostics.Print(label + ".pair." + i + "_" + j + ".solid." + ai + "_" + bi + ".clashCount", clashes == null ? 0 : clashes.Count);
                if (clashes == null) continue;
                int clashIndex = 0;
                foreach (BaseClashResultItem item in clashes) {
                  BaseBody.TypeOfClash clash = item.Type;
                  EasyDiagnostics.Print(label + ".pair." + i + "_" + j + ".solid." + ai + "_" + bi + ".clash." + clashIndex + ".type", clash);
                  if (clash == BaseBody.TypeOfClash.Interfere
                      || clash == BaseBody.TypeOfClash.Exists
                      || clash == BaseBody.TypeOfClash.TargetInTool
                      || clash == BaseBody.TypeOfClash.ToolInTarget) pairClashed = true;
                  else if (clash == BaseBody.TypeOfClash.Abutment) report.ContactCount++;
                  clashIndex++;
                }
              }
            }
            EasyDiagnostics.Print(label + ".pair." + i + "_" + j + ".solidBodyPairCount", bodyPairCount);
          } catch (Exception ex) {
            EasyDiagnostics.Print(label + ".pair." + i + "_" + j + ".exactClashError", ex.GetType().Name + ": " + ex.Message);
          }
          EasyDiagnostics.Print(label + ".pair." + i + "_" + j + ".collisionMethod", "AABB+Clash");
          EasyDiagnostics.Print(label + ".pair." + i + "_" + j + ".trueIntersect", pairClashed);
          if (pairClashed) report.CollisionCount++;
        }
      }
    }

    public static HashSet<Operation> ValidateMates(Document doc, AssemblyValidationReport report, string label) {
      HashSet<Operation> mateConnectedOperations = new HashSet<Operation>();
      ICollection<Mate> mates = Document3D.GetMates(doc);
      report.MateCount = mates.Count;
      EasyDiagnostics.Print(label + ".mateCount", mates.Count);
      int index = 0;
      foreach (Mate mate in mates) {
        Operation op1 = null;
        Operation op2 = null;
        try { op1 = mate.Operation1; } catch (Exception ex) { EasyDiagnostics.Print(label + ".mate." + index + ".operation1Error", ex.GetType().Name + ": " + ex.Message); }
        try { op2 = mate.Operation2; } catch (Exception ex) { EasyDiagnostics.Print(label + ".mate." + index + ".operation2Error", ex.GetType().Name + ": " + ex.Message); }
        EasyDiagnostics.Print(label + ".mate." + index + ".name", String.IsNullOrWhiteSpace(mate.Name) ? "Mate_" + index : mate.Name);
        EasyDiagnostics.Print(label + ".mate." + index + ".type", mate.Type);
        EasyDiagnostics.Print(label + ".mate." + index + ".element1Null", mate.Element1 == null);
        EasyDiagnostics.Print(label + ".mate." + index + ".element2Null", mate.Element2 == null);
        EasyDiagnostics.Print(label + ".mate." + index + ".operation1Null", op1 == null);
        EasyDiagnostics.Print(label + ".mate." + index + ".operation2Null", op2 == null);
        EasyDiagnostics.Print(label + ".mate." + index + ".operation1Name", OperationName(op1, "null"));
        EasyDiagnostics.Print(label + ".mate." + index + ".operation2Name", OperationName(op2, "null"));
        try {
          EasyDiagnostics.Print(label + ".mate." + index + ".suppressed", mate.Suppressed == null ? "null" : mate.Suppressed.ToString());
        } catch (Exception ex) {
          EasyDiagnostics.Print(label + ".mate." + index + ".suppressedError", ex.GetType().Name + ": " + ex.Message);
        }
        if (op1 != null) {
          report.MateOperationLinkCount++;
          mateConnectedOperations.Add(op1);
        }
        if (op2 != null) {
          report.MateOperationLinkCount++;
          mateConnectedOperations.Add(op2);
        }
        if (op1 != null && op2 != null) report.MateEdgeCount++;
        index++;
      }
      return mateConnectedOperations;
    }

    public static void ValidateFragments(Document doc, AssemblyValidationReport report, string label, HashSet<Operation> mateConnectedOperations) {
      int index = 0;
      foreach (Operation op in Document3D.GetOperations(doc)) {
        Fragment3D fragment = op as Fragment3D;
        if (fragment == null) continue;
        report.FragmentCount++;
        bool connected = false;
        bool connectedByLcs = false;
        bool connectedByMate = mateConnectedOperations != null && mateConnectedOperations.Contains(op);
        string reason = "";
        try {
          Fragment3D.FixingType fixing = fragment.Fixing;
          bool targetLcsNull = fragment.TargetLCS == null;
          string source = "";
          try { source = fragment.SourceLCSName; } catch {}
          EasyDiagnostics.Print(label + ".fragment." + index + ".name", String.IsNullOrWhiteSpace(fragment.Name) ? "Fragment3D_" + index : fragment.Name);
          EasyDiagnostics.Print(label + ".fragment." + index + ".fixing", fixing);
          EasyDiagnostics.Print(label + ".fragment." + index + ".sourceLcs", source);
          EasyDiagnostics.Print(label + ".fragment." + index + ".targetLcsNull", targetLcsNull);
          EasyDiagnostics.Print(label + ".fragment." + index + ".connectedByMate", connectedByMate);
          connectedByLcs = fixing != Fragment3D.FixingType.NoFixing && !targetLcsNull;
          connected = connectedByLcs || connectedByMate;
          reason = connectedByLcs ? "connected_by_target_lcs" : (connectedByMate ? "connected_by_mate_operation" : "no_lcs_fixing_or_mate");
        } catch (Exception ex) {
          reason = "fragment_fixing_read_error:" + ex.GetType().Name;
          EasyDiagnostics.Print(label + ".fragment." + index + ".error", ex.GetType().Name + ": " + ex.Message);
        }
        if (connectedByMate) report.MateLinkedFragmentCount++;
        EasyDiagnostics.Print(label + ".fragment." + index + ".connected", connected);
        EasyDiagnostics.Print(label + ".fragment." + index + ".reason", reason);
        if (connected) report.ConnectedFragmentCount++;
        else report.FloatingFragmentCount++;
        index++;
      }
    }

    public static string OperationName(Operation op, string fallback) {
      if (op == null) return fallback;
      if (String.IsNullOrWhiteSpace(op.Name)) return op.GetType().Name;
      return op.Name;
    }

    public static bool BoxesOverlap(BodyBoxMm a, BodyBoxMm b) {
      if (!a.Valid || !b.Valid) return false;
      return a.MinX < b.MaxX && a.MaxX > b.MinX
          && a.MinY < b.MaxY && a.MaxY > b.MinY
          && a.MinZ < b.MaxZ && a.MaxZ > b.MinZ;
    }

    public static void PrintReport(AssemblyValidationReport report, string label) {
      EasyDiagnostics.Print(label + ".summary.bodyCount", report.BodyCount);
      EasyDiagnostics.Print(label + ".summary.bboxOverlapCount", report.BBoxOverlapCount);
      EasyDiagnostics.Print(label + ".summary.clashPairCount", report.ClashPairCount);
      EasyDiagnostics.Print(label + ".summary.collisionCount", report.CollisionCount);
      EasyDiagnostics.Print(label + ".summary.contactCount", report.ContactCount);
      EasyDiagnostics.Print(label + ".summary.mateCount", report.MateCount);
      EasyDiagnostics.Print(label + ".summary.mateEdgeCount", report.MateEdgeCount);
      EasyDiagnostics.Print(label + ".summary.mateOperationLinkCount", report.MateOperationLinkCount);
      EasyDiagnostics.Print(label + ".summary.mateLinkedFragmentCount", report.MateLinkedFragmentCount);
      EasyDiagnostics.Print(label + ".summary.fragmentCount", report.FragmentCount);
      EasyDiagnostics.Print(label + ".summary.connectedFragmentCount", report.ConnectedFragmentCount);
      EasyDiagnostics.Print(label + ".summary.floatingFragmentCount", report.FloatingFragmentCount);
    }
  }
}
