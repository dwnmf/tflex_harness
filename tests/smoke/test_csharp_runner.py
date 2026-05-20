from pathlib import Path

from tflex_harness.runner import run_csharp_snippet


def test_csharp_hello_snippet_runs():
    code = 'public class Program { public static int Main(){ System.Console.WriteLine("hello-from-csharp"); return 0; } }'
    result = run_csharp_snippet(code, mode="run", timeout_sec=20, references=[], artifact_prefix="test_csharp_hello")
    assert result["ok"] is True, result
    assert result["stage"] == "run"
    assert "hello-from-csharp" in result["stdout"]
    assert result["resolved_references"] == []


def test_csharp_runner_writes_structured_run_files():
    code = 'public class Program { public static int Main(){ System.Console.WriteLine("structured-files"); return 0; } }'
    result = run_csharp_snippet(code, mode="run", timeout_sec=20, references=[], artifact_prefix="test_csharp_structured_files")
    assert result["ok"] is True, result
    expected = {
        "request.json",
        "snippet.cs",
        "result.json",
        "stdout.txt",
        "stderr.txt",
        "build.log",
        "run.log",
    }
    run_dir = result["run_dir"]
    for name in expected:
        assert (Path(run_dir) / name).exists(), result
    assert result["snippet_path"].endswith("snippet.cs")


def test_csharp_compile_error_is_structured():
    code = 'public class Program { public static int Main(){ MissingType x = null; return 0; } }'
    result = run_csharp_snippet(code, mode="compile_only", timeout_sec=20, references=[], artifact_prefix="test_csharp_compile_error")
    assert result["ok"] is False
    assert result["stage"] == "compile"
    assert any(d["code"] == "CS0246" for d in result["diagnostics"]), result


def test_csharp_compile_cache_reuses_successful_build():
    code = 'public class Program { public static int Main(){ System.Console.WriteLine("hello-cache"); return 0; } }'
    first = run_csharp_snippet(code, mode="compile_only", timeout_sec=20, references=[], artifact_prefix="test_csharp_cache_first")
    second = run_csharp_snippet(code, mode="compile_only", timeout_sec=20, references=[], artifact_prefix="test_csharp_cache_second")
    assert first["ok"] is True, first
    assert second["ok"] is True, second
    assert first["cache_key"] == second["cache_key"]
    assert second["cache_hit"] is True
    assert second["resolved_references"] == []


def test_csharp_runner_reports_selected_references():
    code = r'''
using System;
using System.Reflection;
public class Program {
  public static int Main(){
    Console.WriteLine(Assembly.Load("TFlexAPI").GetName().Name);
    return 0;
  }
}
'''
    result = run_csharp_snippet(code, mode="compile_only", timeout_sec=30, references=["TFlexAPI"], artifact_prefix="test_csharp_selected_reference")

    assert result["ok"] is True, result
    assert result["resolved_references"][0]["name"] == "TFlexAPI"
    assert result["resolved_references"][0]["dll"] == "TFlexAPI.dll"
    assert result["resolved_references"][0]["exists"] is True
    assert result["resolved_references"][0]["path"].endswith("TFlexAPI.dll")


def test_csharp_runner_missing_reference_keeps_repro_artifacts():
    code = 'public class Program { public static int Main(){ return 0; } }'
    result = run_csharp_snippet(code, mode="compile_only", timeout_sec=20, references=["NoSuchTFlexAssembly"], artifact_prefix="test_csharp_missing_reference")

    assert result["ok"] is False
    assert result["stage"] == "environment"
    assert result["error"] == "missing references"
    assert result["missing_references"][0].endswith("NoSuchTFlexAssembly.dll")
    assert result["snippet_path"].endswith("snippet.cs")
    assert result["artifacts_dir"].endswith("artifacts")
    assert (Path(result["run_dir"]) / "request.json").exists()
    assert (Path(result["run_dir"]) / "snippet.cs").exists()
    assert (Path(result["run_dir"]) / "result.json").exists()


def test_csharp_runner_reports_snippet_artifacts():
    code = r'''
using System;
using System.IO;
public class Program {
  public static int Main(){
    string dir = Environment.GetEnvironmentVariable("TFLEX_HARNESS_ARTIFACTS_DIR");
    Directory.CreateDirectory(dir);
    File.WriteAllText(Path.Combine(dir, "probe.txt"), "artifact-ok");
    Console.WriteLine("artifact-dir=" + dir);
    return 0;
  }
}
'''
    result = run_csharp_snippet(code, mode="run", timeout_sec=20, references=[], artifact_prefix="test_csharp_artifact")
    assert result["ok"] is True, result
    assert result["artifacts_dir"]
    assert result["run_log"]
    assert any(item["relative_path"] == "artifacts/probe.txt" and item["size"] == 11 for item in result["artifacts"]), result


def test_csharp_runner_runtime_timeout_is_structured():
    code = r'''
public class Program {
  public static int Main(){
    System.Threading.Thread.Sleep(5000);
    return 0;
  }
}
'''
    compiled = run_csharp_snippet(code, mode="compile_only", timeout_sec=20, references=[], artifact_prefix="test_csharp_timeout_compile")
    assert compiled["ok"] is True, compiled

    result = run_csharp_snippet(code, mode="run", timeout_sec=1, references=[], artifact_prefix="test_csharp_timeout_run")
    assert result["ok"] is False, result
    assert result["stage"] == "timeout"
    assert result["phase"] == "run"
    assert result["timeout_sec"] == 1
    assert result["cache_hit"] is True
