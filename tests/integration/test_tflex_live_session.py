import pytest

from tflex_harness.runner import run_csharp_snippet


@pytest.mark.integration
def test_tflex_api_init_session_readonly_live():
    code = r'''
using System;
using TFlex;
public class Program {
  public static int Main(){
    var setup = new ApplicationSessionSetup();
    setup.ReadOnly = true;
    setup.Enable3D = false;
    setup.EnableDOCs = false;
    setup.EnableMacros = false;
    setup.PromptToSaveModifiedDocuments = false;
    setup.ProtectionLicense = ApplicationSessionSetup.License.TFlexAPI;
    Console.WriteLine("before=" + Application.IsSessionInitialized);
    bool ok = Application.InitSession(setup);
    Console.WriteLine("init=" + ok);
    Console.WriteLine("after=" + Application.IsSessionInitialized);
    if (Application.IsSessionInitialized) Application.ExitSession();
    Console.WriteLine("exited=" + Application.IsSessionInitialized);
    return ok ? 0 : 3;
  }
}
'''
    result = run_csharp_snippet(code, mode="run", timeout_sec=60, artifact_prefix="integration_tflex_init_session_readonly")
    assert result["ok"] is True, result
    assert "init=True" in result["stdout"]
    assert "after=True" in result["stdout"]
    assert "exited=False" in result["stdout"]
