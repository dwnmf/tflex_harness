from tflex_harness.runner import run_csharp_snippet


def test_csharp_hello_snippet_runs():
    code = 'public class Program { public static int Main(){ System.Console.WriteLine("hello-from-csharp"); return 0; } }'
    result = run_csharp_snippet(code, mode="run", timeout_sec=20, references=[], artifact_prefix="test_csharp_hello")
    assert result["ok"] is True, result
    assert result["stage"] == "run"
    assert "hello-from-csharp" in result["stdout"]


def test_csharp_compile_error_is_structured():
    code = 'public class Program { public static int Main(){ MissingType x = null; return 0; } }'
    result = run_csharp_snippet(code, mode="compile_only", timeout_sec=20, references=[], artifact_prefix="test_csharp_compile_error")
    assert result["ok"] is False
    assert result["stage"] == "compile"
    assert any(d["code"] == "CS0246" for d in result["diagnostics"]), result
