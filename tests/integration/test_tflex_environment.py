import pytest

from tflex_harness.diagnostics import TFLEX_DLLS, get_environment
from tflex_harness.runner import run_csharp_snippet


@pytest.mark.integration
def test_tflex_dlls_present():
    env = get_environment()
    missing = [name for name in TFLEX_DLLS if not env["dlls"][name]["exists"]]
    assert not missing


@pytest.mark.integration
def test_compile_references_tflex_assemblies():
    code = r'''
using System;
using System.Reflection;
public class Program {
  public static int Main(){
    foreach (var name in new []{"TFlexAPI", "TFlexAPI3D", "TFlexAPIData", "TFlexCommandAPI"}) {
      var asm = Assembly.Load(name);
      Console.WriteLine(asm.FullName);
    }
    return 0;
  }
}
'''
    result = run_csharp_snippet(code, mode="run", timeout_sec=30, artifact_prefix="integration_tflex_assembly_probe")
    assert result["ok"] is True, result
    assert "TFlexAPI" in result["stdout"]
    assert "TFlexAPI3D" in result["stdout"]
