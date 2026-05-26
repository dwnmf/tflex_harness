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
      ValidateFragments(doc, report, label);
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
          report.CollisionCount++;
          EasyDiagnostics.Print(label + ".pair." + i + "_" + j + ".collisionMethod", "AABB");
        }
      }
    }

    public static void ValidateFragments(Document doc, AssemblyValidationReport report, string label) {
      int index = 0;
      foreach (Operation op in Document3D.GetOperations(doc)) {
        Fragment3D fragment = op as Fragment3D;
        if (fragment == null) continue;
        report.FragmentCount++;
        bool connected = false;
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
          connected = fixing != Fragment3D.FixingType.NoFixing && !targetLcsNull;
          reason = connected ? "connected_by_target_lcs" : "no_lcs_fixing_or_target";
        } catch (Exception ex) {
          reason = "fragment_fixing_read_error:" + ex.GetType().Name;
          EasyDiagnostics.Print(label + ".fragment." + index + ".error", ex.GetType().Name + ": " + ex.Message);
        }
        EasyDiagnostics.Print(label + ".fragment." + index + ".connected", connected);
        EasyDiagnostics.Print(label + ".fragment." + index + ".reason", reason);
        if (connected) report.ConnectedFragmentCount++;
        else report.FloatingFragmentCount++;
        index++;
      }
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
      EasyDiagnostics.Print(label + ".summary.fragmentCount", report.FragmentCount);
      EasyDiagnostics.Print(label + ".summary.connectedFragmentCount", report.ConnectedFragmentCount);
      EasyDiagnostics.Print(label + ".summary.floatingFragmentCount", report.FloatingFragmentCount);
    }
  }
}
