using System;
using System.Collections.Generic;
using System.IO;
using TFlex;
using TFlex.Model;

namespace TFlexEasy {
  public sealed class EasyCommandProbeResult {
    public string Name;
    public bool Started;
    public bool CallbackCalled;
    public string ResultText;
    public string Error;
  }

  public static class EasyCommandProbe {
    public static string[] ListKnownCommands() {
      try {
        string programDir = Environment.GetEnvironmentVariable("TFLEX_PROGRAM_DIR");
        if (String.IsNullOrWhiteSpace(programDir)) programDir = Path.GetDirectoryName(typeof(Application).Assembly.Location);
        string commandDir = Path.Combine(programDir, "CommandInfo");
        EasyDiagnostics.Print("commandProbe.listKnownCommands.path", commandDir);
        if (!Directory.Exists(commandDir)) {
          EasyDiagnostics.Print("commandProbe.listKnownCommands.available", false);
          EasyDiagnostics.Print("commandProbe.listKnownCommands.count", 0);
          return new string[0];
        }
        List<string> names = new List<string>();
        foreach (string path in Directory.GetFiles(commandDir, "*.txt")) {
          names.Add(Path.GetFileNameWithoutExtension(path));
        }
        names.Sort(StringComparer.OrdinalIgnoreCase);
        EasyDiagnostics.Print("commandProbe.listKnownCommands.available", true);
        EasyDiagnostics.Print("commandProbe.listKnownCommands.count", names.Count);
        if (names.Count > 0) EasyDiagnostics.Print("commandProbe.listKnownCommands.first", names[0]);
        if (names.Contains("CreateMate")) EasyDiagnostics.Print("commandProbe.listKnownCommands.hasCreateMate", true);
        return names.ToArray();
      } catch (Exception ex) {
        EasyDiagnostics.Print("commandProbe.listKnownCommands.available", false);
        EasyDiagnostics.Print("commandProbe.listKnownCommands.error", ex.GetType().Name + ": " + ex.Message);
        return new string[0];
      }
    }

    public static EasyCommandProbeResult TryRunSystemCommand(string name, ModelObject[] objects) {
      EasyCommandProbeResult result = new EasyCommandProbeResult();
      result.Name = name;
      try {
        Application.RunSystemCommand(name, objects ?? new ModelObject[0], delegate(SystemCommandFinishedResult finished) {
          result.CallbackCalled = true;
          result.ResultText = finished == null ? "null" : finished.ToString();
        });
        result.Started = true;
      } catch (Exception ex) {
        result.Error = ex.GetType().Name + ": " + ex.Message;
      }
      PrintCommandResult(result);
      return result;
    }

    public static void PrintCommandResult(EasyCommandProbeResult result) {
      EasyDiagnostics.Print("commandProbe.name", result == null ? "null" : result.Name);
      EasyDiagnostics.Print("commandProbe.started", result != null && result.Started);
      EasyDiagnostics.Print("commandProbe.callbackCalled", result != null && result.CallbackCalled);
      EasyDiagnostics.Print("commandProbe.result", result == null ? "null" : result.ResultText);
      EasyDiagnostics.Print("commandProbe.error", result == null ? "null" : result.Error);
    }
  }
}
