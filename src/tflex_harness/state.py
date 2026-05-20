from __future__ import annotations

import re
from typing import Any

from .runner import run_csharp_snippet

CAPTURE_STATE_CODE = r'''
using System;
using TFlex;
using TFlex.Model;
public class Program {
  public static int Main(){
    var setup = new ApplicationSessionSetup();
    setup.ReadOnly = true;
    setup.Enable3D = false;
    setup.EnableDOCs = false;
    setup.EnableMacros = false;
    setup.PromptToSaveModifiedDocuments = false;
    setup.ProtectionLicense = ApplicationSessionSetup.License.TFlexAPI;
    bool init = Application.InitSession(setup);
    Console.WriteLine("init=" + init);
    if (!init) return 10;
    try {
      var active = Application.ActiveDocument;
      Console.WriteLine("activeNull=" + (active == null));
      if (active != null) Console.WriteLine("active=" + active.Title + "|" + active.FileName);
      int count = 0;
      foreach (Document doc in Application.Documents) {
        count++;
        Console.WriteLine("doc=" + doc.Title + "|" + doc.FileName);
      }
      Console.WriteLine("documents=" + count);
      return 0;
    } finally {
      if (Application.IsSessionInitialized) Application.ExitSession();
      Console.WriteLine("session=" + Application.IsSessionInitialized);
    }
  }
}
'''


def _parse_bool(value: str) -> bool | None:
    if value == "True":
        return True
    if value == "False":
        return False
    return None


def capture_tflex_state(timeout_sec: int = 60) -> dict[str, Any]:
    result = run_csharp_snippet(CAPTURE_STATE_CODE, mode="run", timeout_sec=timeout_sec, artifact_prefix="capture_tflex_state")
    state: dict[str, Any] = {
        "ok": result.get("ok") is True,
        "run": result,
        "session_initialized": None,
        "active_document": None,
        "document_count": None,
        "documents": [],
    }
    for line in (result.get("stdout") or "").splitlines():
        if line.startswith("init="):
            state["session_initialized"] = _parse_bool(line.split("=", 1)[1])
        elif line.startswith("activeNull="):
            active_null = _parse_bool(line.split("=", 1)[1])
            if active_null is True:
                state["active_document"] = None
        elif line.startswith("active="):
            title, _, file_name = line.split("=", 1)[1].partition("|")
            state["active_document"] = {"title": title, "file_name": file_name}
        elif line.startswith("doc="):
            title, _, file_name = line.split("=", 1)[1].partition("|")
            state["documents"].append({"title": title, "file_name": file_name})
        elif line.startswith("documents="):
            try:
                state["document_count"] = int(line.split("=", 1)[1])
            except ValueError:
                pass
    if state["document_count"] is None:
        state["document_count"] = len(state["documents"])
    return state
