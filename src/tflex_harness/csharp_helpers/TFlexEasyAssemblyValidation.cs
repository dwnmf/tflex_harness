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
    public int BroadPhasePairCount;
    public int BBoxOverlapCount;
    public int BBoxContactCandidateCount;
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
    public int GroundedFragmentCount;
    public int UngroundedFragmentCount;
    public int FullyConstrainedFragmentCount;
    public int UnderConstrainedFragmentCount;
    public int OverConstrainedSuspectedFragmentCount;
    public int EstimatedDofTotal;
    public int EstimatedDofRemaining;
    public int EstimatedConstraintCount;
  }

  public sealed class MateEdgeRecord {
    public Operation Operation1;
    public Operation Operation2;
    public Mate.MateType Type;
    public int ConstraintCount;
  }

  public sealed class MateAnalysisResult {
    public HashSet<Operation> LinkedOperations = new HashSet<Operation>();
    public List<MateEdgeRecord> Edges = new List<MateEdgeRecord>();
  }

  public static class EasyAssemblyValidation {
    public static AssemblyValidationReport Validate(Document doc, string label) {
      AssemblyValidationReport report = new AssemblyValidationReport();
      List<AssemblyBodyRecord> bodies = CollectBodies(doc, label);
      report.BodyCount = bodies.Count;
      ValidateBodyClashes(bodies, report, label);
      MateAnalysisResult mates = ValidateMates(doc, report, label);
      ValidateFragments(doc, report, label, mates);
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
          bool broadPhaseCandidate = BoxesMayTouchOrOverlap(a.Box, b.Box, 0.001);
          EasyDiagnostics.Print(label + ".pair." + i + "_" + j + ".bboxOverlap", bboxOverlap);
          EasyDiagnostics.Print(label + ".pair." + i + "_" + j + ".broadPhaseCandidate", broadPhaseCandidate);
          if (!broadPhaseCandidate) continue;
          report.BroadPhasePairCount++;
          if (bboxOverlap) report.BBoxOverlapCount++;
          else report.BBoxContactCandidateCount++;
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
                  if (IsCollisionClash(clash)) {
                    if (bboxOverlap) pairClashed = true;
                    else {
                      report.ContactCount++;
                      EasyDiagnostics.Print(label + ".pair." + i + "_" + j + ".solid." + ai + "_" + bi + ".clash." + clashIndex + ".classification", "contact_by_bbox_no_volume_overlap");
                    }
                  } else if (clash == BaseBody.TypeOfClash.Abutment) {
                    report.ContactCount++;
                    EasyDiagnostics.Print(label + ".pair." + i + "_" + j + ".solid." + ai + "_" + bi + ".clash." + clashIndex + ".classification", "contact_by_kernel_abutment");
                  }
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

    public static MateAnalysisResult ValidateMates(Document doc, AssemblyValidationReport report, string label) {
      MateAnalysisResult analysis = new MateAnalysisResult();
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
          analysis.LinkedOperations.Add(op1);
        }
        if (op2 != null) {
          report.MateOperationLinkCount++;
          analysis.LinkedOperations.Add(op2);
        }
        if (op1 != null && op2 != null) {
          report.MateEdgeCount++;
          int constraints = EstimateMateConstraintCount(mate.Type);
          analysis.Edges.Add(new MateEdgeRecord { Operation1 = op1, Operation2 = op2, Type = mate.Type, ConstraintCount = constraints });
          EasyDiagnostics.Print(label + ".mate." + index + ".estimatedConstraintCount", constraints);
        }
        index++;
      }
      return analysis;
    }

    public static void ValidateFragments(Document doc, AssemblyValidationReport report, string label, MateAnalysisResult mates) {
      HashSet<Operation> fixedRoots = new HashSet<Operation>();
      List<Fragment3D> fragments = new List<Fragment3D>();
      foreach (Operation op in Document3D.GetOperations(doc)) {
        Fragment3D fragment = op as Fragment3D;
        if (fragment == null) continue;
        fragments.Add(fragment);
        if (IsFragmentFixedByLcs(fragment)) fixedRoots.Add(fragment);
      }
      HashSet<Operation> groundedByGraph = BuildGroundedOperationSet(fixedRoots, mates);
      int index = 0;
      foreach (Fragment3D fragment in fragments) {
        Operation op = fragment;
        report.FragmentCount++;
        bool connectedByLcs = false;
        bool connectedByMate = mates != null && mates.LinkedOperations.Contains(op);
        bool grounded = groundedByGraph.Contains(op);
        string reason = "";
        int mateConstraints = SumMateConstraints(op, mates);
        int lcsConstraints = 0;
        int estimatedConstraints = 0;
        int remainingDof = 6;
        bool overConstrained = false;
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
          lcsConstraints = connectedByLcs ? 6 : 0;
          estimatedConstraints = lcsConstraints + mateConstraints;
          overConstrained = estimatedConstraints > 6;
          remainingDof = overConstrained ? 0 : Math.Max(0, 6 - estimatedConstraints);
          if (connectedByLcs) reason = "grounded_by_target_lcs";
          else if (grounded && connectedByMate) reason = "grounded_by_mate_path";
          else if (connectedByMate) reason = "mate_linked_but_not_grounded";
          else reason = "no_lcs_fixing_or_mate";
        } catch (Exception ex) {
          reason = "fragment_fixing_read_error:" + ex.GetType().Name;
          EasyDiagnostics.Print(label + ".fragment." + index + ".error", ex.GetType().Name + ": " + ex.Message);
        }
        if (connectedByMate) report.MateLinkedFragmentCount++;
        EasyDiagnostics.Print(label + ".fragment." + index + ".grounded", grounded);
        EasyDiagnostics.Print(label + ".fragment." + index + ".lcsConstraintCount", lcsConstraints);
        EasyDiagnostics.Print(label + ".fragment." + index + ".mateConstraintCount", mateConstraints);
        EasyDiagnostics.Print(label + ".fragment." + index + ".estimatedConstraintCount", estimatedConstraints);
        EasyDiagnostics.Print(label + ".fragment." + index + ".estimatedRemainingDof", remainingDof);
        EasyDiagnostics.Print(label + ".fragment." + index + ".overConstrainedSuspected", overConstrained);
        EasyDiagnostics.Print(label + ".fragment." + index + ".connected", grounded);
        EasyDiagnostics.Print(label + ".fragment." + index + ".reason", reason);
        report.EstimatedDofTotal += 6;
        report.EstimatedConstraintCount += estimatedConstraints;
        report.EstimatedDofRemaining += remainingDof;
        if (grounded) {
          report.ConnectedFragmentCount++;
          report.GroundedFragmentCount++;
        } else {
          report.FloatingFragmentCount++;
          report.UngroundedFragmentCount++;
        }
        if (overConstrained) report.OverConstrainedSuspectedFragmentCount++;
        else if (remainingDof == 0 && grounded) report.FullyConstrainedFragmentCount++;
        else report.UnderConstrainedFragmentCount++;
        index++;
      }
    }

    public static bool IsFragmentFixedByLcs(Fragment3D fragment) {
      try {
        return fragment.Fixing != Fragment3D.FixingType.NoFixing && fragment.TargetLCS != null;
      } catch {
        return false;
      }
    }

    public static HashSet<Operation> BuildGroundedOperationSet(HashSet<Operation> fixedRoots, MateAnalysisResult mates) {
      HashSet<Operation> grounded = new HashSet<Operation>();
      Queue<Operation> queue = new Queue<Operation>();
      foreach (Operation root in fixedRoots) {
        if (root == null || grounded.Contains(root)) continue;
        grounded.Add(root);
        queue.Enqueue(root);
      }
      if (mates == null) return grounded;
      while (queue.Count > 0) {
        Operation current = queue.Dequeue();
        foreach (MateEdgeRecord edge in mates.Edges) {
          Operation next = null;
          if (SameOperation(edge.Operation1, current)) next = edge.Operation2;
          else if (SameOperation(edge.Operation2, current)) next = edge.Operation1;
          if (next == null || grounded.Contains(next)) continue;
          grounded.Add(next);
          queue.Enqueue(next);
        }
      }
      return grounded;
    }

    public static int SumMateConstraints(Operation op, MateAnalysisResult mates) {
      if (op == null || mates == null) return 0;
      int sum = 0;
      foreach (MateEdgeRecord edge in mates.Edges) {
        if (SameOperation(edge.Operation1, op) || SameOperation(edge.Operation2, op)) sum += edge.ConstraintCount;
      }
      return sum;
    }

    public static bool SameOperation(Operation a, Operation b) {
      if (a == null || b == null) return false;
      if (Object.ReferenceEquals(a, b)) return true;
      return Object.Equals(a, b);
    }

    public static int EstimateMateConstraintCount(Mate.MateType type) {
      switch (type) {
        case Mate.MateType.Coincidence: return 3;
        case Mate.MateType.Concentricity: return 4;
        case Mate.MateType.Parallelism: return 2;
        case Mate.MateType.Perpendicularity: return 2;
        case Mate.MateType.Tangency: return 1;
        case Mate.MateType.Distance: return 1;
        case Mate.MateType.Angle: return 1;
        case Mate.MateType.AngAngTransmission: return 1;
        case Mate.MateType.AngLinTransmission: return 1;
        case Mate.MateType.LinLinTransmission: return 1;
        default: return 1;
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

    public static bool IsCollisionClash(BaseBody.TypeOfClash clash) {
      return clash == BaseBody.TypeOfClash.Interfere
          || clash == BaseBody.TypeOfClash.Exists
          || clash == BaseBody.TypeOfClash.TargetInTool
          || clash == BaseBody.TypeOfClash.ToolInTarget;
    }

    public static bool BoxesMayTouchOrOverlap(BodyBoxMm a, BodyBoxMm b, double toleranceMm) {
      if (!a.Valid || !b.Valid) return false;
      return a.MinX <= b.MaxX + toleranceMm && a.MaxX + toleranceMm >= b.MinX
          && a.MinY <= b.MaxY + toleranceMm && a.MaxY + toleranceMm >= b.MinY
          && a.MinZ <= b.MaxZ + toleranceMm && a.MaxZ + toleranceMm >= b.MinZ;
    }

    public static void PrintReport(AssemblyValidationReport report, string label) {
      EasyDiagnostics.Print(label + ".summary.bodyCount", report.BodyCount);
      EasyDiagnostics.Print(label + ".summary.broadPhasePairCount", report.BroadPhasePairCount);
      EasyDiagnostics.Print(label + ".summary.bboxOverlapCount", report.BBoxOverlapCount);
      EasyDiagnostics.Print(label + ".summary.bboxContactCandidateCount", report.BBoxContactCandidateCount);
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
      EasyDiagnostics.Print(label + ".summary.groundedFragmentCount", report.GroundedFragmentCount);
      EasyDiagnostics.Print(label + ".summary.ungroundedFragmentCount", report.UngroundedFragmentCount);
      EasyDiagnostics.Print(label + ".summary.fullyConstrainedFragmentCount", report.FullyConstrainedFragmentCount);
      EasyDiagnostics.Print(label + ".summary.underConstrainedFragmentCount", report.UnderConstrainedFragmentCount);
      EasyDiagnostics.Print(label + ".summary.overConstrainedSuspectedFragmentCount", report.OverConstrainedSuspectedFragmentCount);
      EasyDiagnostics.Print(label + ".summary.estimatedDofTotal", report.EstimatedDofTotal);
      EasyDiagnostics.Print(label + ".summary.estimatedConstraintCount", report.EstimatedConstraintCount);
      EasyDiagnostics.Print(label + ".summary.estimatedDofRemaining", report.EstimatedDofRemaining);
    }
  }
}
