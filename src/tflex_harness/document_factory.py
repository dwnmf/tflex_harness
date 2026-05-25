from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

from .artifacts import ArtifactStore, json_default
from .config import HarnessConfig, load_config
from .prototypes import find_prototype
from .recipes import run_recipe
from .runner import run_csharp_snippet


def create_document_from_payload(
    payload_path: str | Path,
    *,
    timeout_sec: int = 120,
    dry_run: bool = False,
    config: HarnessConfig | None = None,
    recipe_runner=run_recipe,
) -> dict[str, Any]:
    cfg = config or load_config()
    path = Path(payload_path).resolve()
    if not path.exists():
        return {"ok": False, "stage": "input", "error": "payload file does not exist", "payload_path": str(path)}

    try:
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as exc:
        return {"ok": False, "stage": "input", "error": "payload JSON is invalid", "payload_path": str(path), "detail": str(exc)}

    if not isinstance(payload, dict):
        return {"ok": False, "stage": "input", "error": "payload root must be an object", "payload_path": str(path)}

    plan = plan_document_creation(payload)
    store = ArtifactStore(cfg)
    factory_dir = store.create_run_dir("document_factory")
    input_copy = factory_dir / "input_payload.json"
    input_copy.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=json_default) + "\n", encoding="utf-8")
    plan_path = factory_dir / "factory_plan.json"

    result: dict[str, Any] = {
        "ok": plan["ok"] if dry_run else False,
        "stage": "dry_run" if dry_run else "run",
        "payload_path": str(path),
        "factory_run_dir": str(factory_dir),
        "input_payload_path": str(input_copy),
        "plan_path": str(plan_path),
        "plan": plan,
        "dry_run": dry_run,
    }
    plan_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2, default=json_default) + "\n", encoding="utf-8")

    if not plan["ok"]:
        result["ok"] = False
        result["stage"] = "input"
        return result
    if dry_run:
        return result

    if plan["recipe"] == "__factory_multi_step":
        recipe_result = _run_multi_step_plan(plan, factory_dir=factory_dir, timeout_sec=timeout_sec, config=cfg)
    else:
        recipe_result = recipe_runner(plan["recipe"], args=plan["recipe_args"], timeout_sec=timeout_sec, config=cfg)
    outputs_result = _materialize_requested_outputs(plan, recipe_result, factory_dir, timeout_sec=timeout_sec, config=cfg)
    result["recipe_result"] = recipe_result
    result["outputs"] = outputs_result["outputs"]
    result["output_errors"] = outputs_result["errors"]
    result["ok"] = recipe_result.get("ok") is True and not outputs_result["errors"]
    result["stage"] = recipe_result.get("stage", "run")
    result["recipe"] = plan["recipe"]
    result["recipe_args"] = plan["recipe_args"]
    result["recipe_run_dir"] = recipe_result.get("run_dir")
    (factory_dir / "factory_result.json").write_text(json.dumps(result, ensure_ascii=False, indent=2, default=json_default) + "\n", encoding="utf-8")
    return result


def plan_document_creation(payload: dict[str, Any]) -> dict[str, Any]:
    prototype_args = _prototype_args(payload.get("prototype"))
    if prototype_args.get("ok") is False:
        return prototype_args
    output_contract = _output_contract(payload.get("output"))
    if output_contract.get("ok") is False:
        return output_contract

    explicit = payload.get("recipe")
    if isinstance(explicit, dict):
        recipe_name = explicit.get("name")
        recipe_args = dict(explicit.get("args") or {})
        if not recipe_name:
            return {"ok": False, "stage": "input", "error": "recipe.name is required"}
        recipe_args = {**prototype_args["args"], **recipe_args}
        return _plan(str(recipe_name), recipe_args, payload, selection="explicit_recipe", output=output_contract)
    if isinstance(explicit, str) and explicit:
        return _plan(explicit, dict(prototype_args["args"]), payload, selection="explicit_recipe", output=output_contract)

    document = payload.get("document") or {}
    if not isinstance(document, dict):
        return {"ok": False, "stage": "input", "error": "document must be an object"}

    operations = _collect_operations(document)
    if isinstance(operations, dict) and operations.get("ok") is False:
        return operations
    if len(operations) > 1:
        return {
            "ok": True,
            "recipe": "__factory_multi_step",
            "recipe_args": dict(prototype_args["args"]),
            "selection": "multi_step",
            "operations": operations,
            "output": output_contract["output"],
            "limitations": [
                "Phase 6 multi-step factory uses generated visible C# with checked-in helper sources.",
                "GRB, STEP, PDF, DXF, and DWG output materialization are implemented in this phase.",
            ],
            "pending_operations": [],
        }

    properties = document.get("properties") or {}
    if isinstance(properties, dict) and properties:
        name, value = next(iter(properties.items()))
        args = {**prototype_args["args"], "property_name": str(name), "text_value": "" if value is None else str(value)}
        return _plan("prototype_set_document_property", args, payload, selection="document.properties", output=output_contract)

    variables = document.get("variables") or {}
    if isinstance(variables, dict) and variables:
        name, value = next(iter(variables.items()))
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            args = {**prototype_args["args"], "variable_name": str(name), "real_value": str(value)}
            return _plan("prototype_set_real_variable", args, payload, selection="document.variables.real", output=output_contract)
        args = {**prototype_args["args"], "variable_name": str(name), "text_value": "" if value is None else str(value)}
        return _plan("prototype_set_text_variable", args, payload, selection="document.variables.text", output=output_contract)

    replacements = document.get("text_replacements") or {}
    if isinstance(replacements, dict) and replacements:
        search, replacement = next(iter(replacements.items()))
        args = {**prototype_args["args"], "search_text": str(search), "replacement_text": "" if replacement is None else str(replacement)}
        return _plan("prototype_replace_visible_text", args, payload, selection="document.text_replacements", output=output_contract)

    tables = document.get("tables") or []
    if isinstance(tables, list) and tables:
        first = tables[0]
        if not isinstance(first, dict):
            return {"ok": False, "stage": "input", "error": "document.tables[0] must be an object"}
        if "cell_index" not in first:
            return {"ok": False, "stage": "input", "error": "document.tables[0].cell_index is required"}
        value = first.get("text_value", first.get("value", ""))
        args = {**prototype_args["args"], "cell_index": str(first["cell_index"]), "text_value": "" if value is None else str(value)}
        return _plan("prototype_set_table_cell", args, payload, selection="document.tables", output=output_contract)

    return _plan("prototype_open_copy_save", dict(prototype_args["args"]), payload, selection="open_copy_save", output=output_contract)


def _collect_operations(document: dict[str, Any]) -> list[dict[str, Any]] | dict[str, Any]:
    operations: list[dict[str, Any]] = []
    properties = document.get("properties") or {}
    if isinstance(properties, dict):
        for name, value in properties.items():
            operations.append({"type": "property", "name": str(name), "value": "" if value is None else str(value)})
    elif properties:
        return {"ok": False, "stage": "input", "error": "document.properties must be an object"}

    variables = document.get("variables") or {}
    if isinstance(variables, dict):
        for name, value in variables.items():
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                operations.append({"type": "real_variable", "name": str(name), "value": value})
            else:
                operations.append({"type": "text_variable", "name": str(name), "value": "" if value is None else str(value)})
    elif variables:
        return {"ok": False, "stage": "input", "error": "document.variables must be an object"}

    replacements = document.get("text_replacements") or {}
    if isinstance(replacements, dict):
        for search, replacement in replacements.items():
            operations.append({"type": "visible_text", "search": str(search), "replacement": "" if replacement is None else str(replacement)})
    elif replacements:
        return {"ok": False, "stage": "input", "error": "document.text_replacements must be an object"}

    tables = document.get("tables") or []
    if isinstance(tables, list):
        for index, item in enumerate(tables):
            if not isinstance(item, dict):
                return {"ok": False, "stage": "input", "error": f"document.tables[{index}] must be an object"}
            if "cell_index" not in item:
                return {"ok": False, "stage": "input", "error": f"document.tables[{index}].cell_index is required"}
            try:
                cell_index = int(item["cell_index"])
            except (TypeError, ValueError):
                return {"ok": False, "stage": "input", "error": f"document.tables[{index}].cell_index must be an integer"}
            value = item.get("text_value", item.get("value", ""))
            operations.append({"type": "table_cell", "cell_index": cell_index, "value": "" if value is None else str(value)})
    elif tables:
        return {"ok": False, "stage": "input", "error": "document.tables must be an array"}
    return operations


def _run_multi_step_plan(plan: dict[str, Any], *, factory_dir: Path, timeout_sec: int, config: HarnessConfig) -> dict[str, Any]:
    source = _resolve_prototype_source(plan["recipe_args"])
    if source.get("ok") is False:
        return source
    code = _generate_multi_step_csharp(plan["operations"])
    snippet_path = factory_dir / "factory_snippet.cs"
    snippet_path.write_text(code, encoding="utf-8", newline="\n")
    result = run_csharp_snippet(
        code,
        mode="run",
        timeout_sec=timeout_sec,
        helpers=["all"],
        environment={"TFLEX_PROTOTYPE_SOURCE_PATH": str(source["source_path"])},
        artifact_prefix="factory_multi_step",
        config=config,
    )
    result["factory_generated_snippet_path"] = str(snippet_path)
    result["factory_source_path"] = str(source["source_path"])
    result["factory_operations"] = plan["operations"]
    return result


def _resolve_prototype_source(args: dict[str, Any]) -> dict[str, Any]:
    if args.get("source_path"):
        path = Path(str(args["source_path"])).resolve()
        if not path.exists():
            return {"ok": False, "stage": "input", "error": "source_path does not exist", "source_path": str(path)}
        return {"ok": True, "source_path": str(path)}
    selector = args.get("prototype_id") or args.get("prototype_selector")
    if not selector:
        return {"ok": False, "stage": "input", "error": "prototype source is required"}
    try:
        return {"ok": True, "source_path": find_prototype(str(selector))["path"]}
    except KeyError as exc:
        return {"ok": False, "stage": "input", "error": str(exc)}


def _generate_multi_step_csharp(operations: list[dict[str, Any]]) -> str:
    body: list[str] = []
    validations: list[str] = []
    for index, operation in enumerate(operations):
        op_type = operation["type"]
        if op_type == "property":
            name = _cs_string(operation["name"])
            value = _cs_string(operation["value"])
            body.append(f'allSet = TFlexEasy.EasyDocumentProperties.SetText(doc, {name}, {value}) && allSet;')
            validations.append(
                f'actual = TFlexEasy.EasyDocumentProperties.Text(reopened, {name}); TFlexEasy.EasyDiagnostics.Print("factory.property.{index}", actual); allValid = (actual == {value}) && allValid;'
            )
        elif op_type == "text_variable":
            name = _cs_string(operation["name"])
            value = _cs_string(operation["value"])
            body.append(f'allSet = TFlexEasy.EasyVariables.SetTextConstant(doc, {name}, {value}) && allSet;')
            validations.append(
                f'actual = TFlexEasy.EasyVariables.TextValue(reopened, {name}); TFlexEasy.EasyDiagnostics.Print("factory.textVariable.{index}", actual); allValid = (actual == {value}) && allValid;'
            )
        elif op_type == "real_variable":
            name = _cs_string(operation["name"])
            value = _cs_double(operation["value"])
            body.append(f'allSet = TFlexEasy.EasyVariables.SetRealConstant(doc, {name}, {value}) && allSet;')
            validations.append(
                f'realActual = TFlexEasy.EasyVariables.RealValue(reopened, {name}); TFlexEasy.EasyDiagnostics.Print("factory.realVariable.{index}", realActual); allValid = (System.Math.Abs(realActual - {value}) < 1e-9) && allValid;'
            )
        elif op_type == "visible_text":
            search = _cs_string(operation["search"])
            replacement = _cs_string(operation["replacement"])
            body.append(f'int hits{index} = TFlexEasy.EasyText.CountVisibleTextOccurrences(doc, {search}); TFlexEasy.EasyDiagnostics.Print("factory.visibleText.before.{index}", hits{index}); int replaced{index} = TFlexEasy.EasyText.ReplaceVisibleText(doc, {search}, {replacement}); allSet = (hits{index} > 0 && replaced{index} == hits{index}) && allSet;')
            validations.append(
                f'int oldAfter{index} = TFlexEasy.EasyText.CountVisibleTextOccurrences(reopened, {search}); int newAfter{index} = TFlexEasy.EasyText.CountVisibleTextOccurrences(reopened, {replacement}); TFlexEasy.EasyDiagnostics.Print("factory.visibleText.oldAfter.{index}", oldAfter{index}); TFlexEasy.EasyDiagnostics.Print("factory.visibleText.newAfter.{index}", newAfter{index}); allValid = (oldAfter{index} == 0 && ({replacement} == "" || newAfter{index} >= replaced{index})) && allValid;'
            )
        elif op_type == "table_cell":
            cell = int(operation["cell_index"])
            value = _cs_string(operation["value"])
            body.append(f'allSet = TFlexEasy.EasyText.SetFirstTableCellText(doc, {cell}u, {value}) && allSet;')
            validations.append(
                f'actual = TFlexEasy.EasyText.FirstTableCellText(reopened, {cell}u); TFlexEasy.EasyDiagnostics.Print("factory.tableCell.{index}", actual); allValid = (actual == {value}) && allValid;'
            )
    needs_actual = any(operation["type"] in {"property", "text_variable", "table_cell"} for operation in operations)
    needs_real_actual = any(operation["type"] == "real_variable" for operation in operations)
    declarations = []
    if needs_actual:
        declarations.append("string actual = null;")
    if needs_real_actual:
        declarations.append("double realActual = 0.0;")
    return f'''using System;
using TFlex.Model;
using TFlexEasy;

public class Program {{
  public static int Main(){{
    string source = Environment.GetEnvironmentVariable("TFLEX_PROTOTYPE_SOURCE_PATH");
    if (String.IsNullOrWhiteSpace(source)) {{
      EasyDiagnostics.Print("prototype.error", "TFLEX_PROTOTYPE_SOURCE_PATH is required");
      return 2;
    }}
    Document doc = null;
    Document reopened = null;
    using (var sess = EasySession.Start3D()) {{
      string copy = sess.ArtifactPath("factory_multi_step_copy.grb");
      string output = sess.ArtifactPath("factory_multi_step_saved.grb");
      try {{
        EasyPrototype.CopyToArtifact(source, copy);
        doc = EasyPrototype.OpenCopy(copy, visible: false);
        bool allSet = true;
        doc.BeginChanges("factory multi-step payload");
        {chr(10).join("        " + line for line in body)}
        var end = doc.EndChanges();
        EasyDiagnostics.Print("endChanges", end);
        EasyDiagnostics.Print("factory.allSet", allSet);
        bool saved = EasyPrototype.SaveAsGrb(doc, output);
        EasyPrototype.Close(doc);
        doc = null;

        reopened = EasyPrototype.OpenCopy(output, visible: false);
        bool allValid = true;
        {chr(10).join("        " + line for line in declarations)}
        {chr(10).join("        " + line for line in validations)}
        EasyDiagnostics.Print("factory.allValid", allValid);
        return (saved && allSet && allValid) ? 0 : 20;
      }} finally {{
        EasyPrototype.Close(reopened);
        EasyPrototype.Close(doc);
      }}
    }}
  }}
}}
'''


def _cs_string(value: Any) -> str:
    text = "" if value is None else str(value)
    return '"' + text.replace("\\", "\\\\").replace('"', '\\"').replace("\r", "\\r").replace("\n", "\\n") + '"'


def _cs_double(value: Any) -> str:
    return format(float(value), ".17g")


def _prototype_args(prototype: Any) -> dict[str, Any]:
    if not isinstance(prototype, dict):
        return {"ok": False, "stage": "input", "error": "prototype object is required"}
    args: dict[str, str] = {}
    if prototype.get("path"):
        args["source_path"] = str(prototype["path"])
    elif prototype.get("id"):
        args["prototype_id"] = str(prototype["id"])
    elif prototype.get("selector"):
        args["prototype_selector"] = str(prototype["selector"])
    else:
        return {"ok": False, "stage": "input", "error": "prototype.id, prototype.path, or prototype.selector is required"}
    return {"ok": True, "args": args}


def _output_contract(output: Any) -> dict[str, Any]:
    if output is None:
        output = {}
    if not isinstance(output, dict):
        return {"ok": False, "stage": "input", "error": "output must be an object"}
    name = str(output.get("name") or "document")
    stem = _safe_output_stem(name)
    exports_raw = output.get("exports", ["grb"])
    if isinstance(exports_raw, str):
        exports = [exports_raw]
    elif isinstance(exports_raw, list):
        exports = [str(item).lower().lstrip(".") for item in exports_raw]
    else:
        return {"ok": False, "stage": "input", "error": "output.exports must be a string or array"}
    exports = exports or ["grb"]
    normalized: list[str] = []
    for item in exports:
        if item and item not in normalized:
            normalized.append(item)
    unsupported = sorted({item for item in normalized if item not in {"grb", "step", "pdf", "dxf", "dwg"}})
    if unsupported:
        return {
            "ok": False,
            "stage": "input",
            "error": "unsupported output export format",
            "unsupported_exports": unsupported,
            "supported_exports": ["grb", "step", "pdf", "dxf", "dwg"],
        }
    return {"ok": True, "output": {"name": stem, "exports": normalized or ["grb"]}}


def _safe_output_stem(name: str) -> str:
    stem = Path(name).stem or name or "document"
    safe = "".join("_" if char in '<>:"/\\|?*' or ord(char) < 32 else char for char in stem)
    safe = safe.strip(" ._")
    return (safe[:80] or "document")


def _materialize_requested_outputs(
    plan: dict[str, Any],
    recipe_result: dict[str, Any],
    factory_dir: Path,
    *,
    timeout_sec: int,
    config: HarnessConfig,
) -> dict[str, Any]:
    output = plan.get("output") or {"name": "document", "exports": ["grb"]}
    outputs: list[dict[str, Any]] = []
    errors: list[str] = []
    exports = output.get("exports", [])
    source = _select_primary_grb(recipe_result)
    if source is None:
        if recipe_result.get("ok") is True:
            errors.append("no GRB artifact found in recipe result")
        return {"outputs": outputs, "errors": errors}
    target_dir = factory_dir / "artifacts" / "outputs"
    target_dir.mkdir(parents=True, exist_ok=True)
    if "grb" in exports:
        target = target_dir / f"{output.get('name') or 'document'}.grb"
        shutil.copy2(source, target)
        outputs.append(_output_record("grb", target, factory_dir, source_path=source))
    if "step" in exports:
        target = target_dir / f"{output.get('name') or 'document'}.step"
        step_result = _export_step_from_grb(source, target, timeout_sec=timeout_sec, config=config)
        if step_result.get("ok") is True and target.exists() and target.stat().st_size > 0:
            record = _output_record("step", target, factory_dir, source_path=source)
            record["export_run_dir"] = step_result.get("run_dir")
            outputs.append(record)
        else:
            errors.append("STEP export failed")
            errors.append(str(step_result.get("error") or step_result.get("stage") or "unknown"))
    if "pdf" in exports:
        target = target_dir / f"{output.get('name') or 'document'}.pdf"
        pdf_result = _export_pdf_from_grb(source, target, timeout_sec=timeout_sec, config=config)
        if pdf_result.get("ok") is True and target.exists() and target.stat().st_size > 0:
            record = _output_record("pdf", target, factory_dir, source_path=source)
            record["export_run_dir"] = pdf_result.get("run_dir")
            outputs.append(record)
        else:
            errors.append("PDF export failed")
            errors.append(str(pdf_result.get("error") or pdf_result.get("stage") or "unknown"))
    if "dxf" in exports:
        dxf_result = _export_acad_from_grb(
            source,
            target_dir / f"{output.get('name') or 'document'}.dxf",
            factory_dir=factory_dir,
            format_name="dxf",
            timeout_sec=timeout_sec,
            config=config,
        )
        if dxf_result["ok"]:
            outputs.append(dxf_result["record"])
        else:
            errors.extend(dxf_result["errors"])
    if "dwg" in exports:
        dwg_result = _export_acad_from_grb(
            source,
            target_dir / f"{output.get('name') or 'document'}.dwg",
            factory_dir=factory_dir,
            format_name="dwg",
            timeout_sec=timeout_sec,
            config=config,
        )
        if dwg_result["ok"]:
            outputs.append(dwg_result["record"])
        else:
            errors.extend(dwg_result["errors"])
    return {"outputs": outputs, "errors": errors}


def _output_record(format_name: str, target: Path, factory_dir: Path, *, source_path: Path) -> dict[str, Any]:
    return {
        "format": format_name,
        "path": str(target),
        "relative_path": str(target.relative_to(factory_dir)).replace("\\", "/"),
        "size": target.stat().st_size,
        "source_path": str(source_path),
    }


def _export_step_from_grb(source_grb: Path, target_step: Path, *, timeout_sec: int, config: HarnessConfig) -> dict[str, Any]:
    code = '''using System;
using TFlex.Model;
using TFlexEasy;

public class Program {
  public static int Main(){
    string source = Environment.GetEnvironmentVariable("TFLEX_FACTORY_EXPORT_SOURCE_GRB");
    string target = Environment.GetEnvironmentVariable("TFLEX_FACTORY_EXPORT_TARGET_STEP");
    if (String.IsNullOrWhiteSpace(source)) {
      EasyDiagnostics.Print("factory.stepExport.error", "TFLEX_FACTORY_EXPORT_SOURCE_GRB is required");
      return 2;
    }
    if (String.IsNullOrWhiteSpace(target)) {
      EasyDiagnostics.Print("factory.stepExport.error", "TFLEX_FACTORY_EXPORT_TARGET_STEP is required");
      return 3;
    }
    Document doc = null;
    using (var sess = EasySession.Start3D()) {
      try {
        doc = EasyPrototype.OpenCopy(source, visible: false);
        bool step = EasyExport.Step(doc, target);
        EasyDiagnostics.Print("factory.stepExport.saved", step);
        return step ? 0 : 20;
      } finally {
        EasyPrototype.Close(doc);
      }
    }
  }
}
'''
    return run_csharp_snippet(
        code,
        mode="run",
        timeout_sec=timeout_sec,
        helpers=["easy_prototype", "easy_export"],
        environment={
            "TFLEX_FACTORY_EXPORT_SOURCE_GRB": str(source_grb),
            "TFLEX_FACTORY_EXPORT_TARGET_STEP": str(target_step),
        },
        artifact_prefix="factory_step_export",
        config=config,
    )


def _export_pdf_from_grb(source_grb: Path, target_pdf: Path, *, timeout_sec: int, config: HarnessConfig) -> dict[str, Any]:
    code = '''using System;
using TFlex.Model;
using TFlexEasy;

public class Program {
  public static int Main(){
    string source = Environment.GetEnvironmentVariable("TFLEX_FACTORY_EXPORT_SOURCE_GRB");
    string target = Environment.GetEnvironmentVariable("TFLEX_FACTORY_EXPORT_TARGET_PDF");
    if (String.IsNullOrWhiteSpace(source)) {
      EasyDiagnostics.Print("factory.pdfExport.error", "TFLEX_FACTORY_EXPORT_SOURCE_GRB is required");
      return 2;
    }
    if (String.IsNullOrWhiteSpace(target)) {
      EasyDiagnostics.Print("factory.pdfExport.error", "TFLEX_FACTORY_EXPORT_TARGET_PDF is required");
      return 3;
    }
    Document doc = null;
    using (var sess = EasySession.Start3D()) {
      try {
        doc = EasyPrototype.OpenCopy(source, visible: false);
        bool pdf = EasyExport.Pdf(doc, target);
        EasyDiagnostics.Print("factory.pdfExport.saved", pdf);
        return pdf ? 0 : 20;
      } finally {
        EasyPrototype.Close(doc);
      }
    }
  }
}
'''
    return run_csharp_snippet(
        code,
        mode="run",
        timeout_sec=timeout_sec,
        helpers=["easy_prototype", "easy_export"],
        environment={
            "TFLEX_FACTORY_EXPORT_SOURCE_GRB": str(source_grb),
            "TFLEX_FACTORY_EXPORT_TARGET_PDF": str(target_pdf),
        },
        artifact_prefix="factory_pdf_export",
        config=config,
    )


def _export_acad_from_grb(
    source_grb: Path,
    target: Path,
    *,
    factory_dir: Path,
    format_name: str,
    timeout_sec: int,
    config: HarnessConfig,
) -> dict[str, Any]:
    export_result = _run_acad_export_from_grb(source_grb, target, format_name=format_name, timeout_sec=timeout_sec, config=config)
    if export_result.get("ok") is True and target.exists() and target.stat().st_size > 0:
        record = _output_record(format_name, target, factory_dir, source_path=source_grb)
        record["export_run_dir"] = export_result.get("run_dir")
        return {"ok": True, "record": record, "errors": []}
    return {
        "ok": False,
        "record": None,
        "errors": [f"{format_name.upper()} export failed", str(export_result.get("error") or export_result.get("stage") or "unknown")],
    }


def _run_acad_export_from_grb(source_grb: Path, target: Path, *, format_name: str, timeout_sec: int, config: HarnessConfig) -> dict[str, Any]:
    method = "Dxf" if format_name == "dxf" else "Dwg"
    env_target = "TFLEX_FACTORY_EXPORT_TARGET_" + format_name.upper()
    code = '''using System;
using TFlex.Model;
using TFlexEasy;

public class Program {
  public static int Main(){
    string source = Environment.GetEnvironmentVariable("TFLEX_FACTORY_EXPORT_SOURCE_GRB");
    string target = Environment.GetEnvironmentVariable("''' + env_target + '''");
    if (String.IsNullOrWhiteSpace(source)) {
      EasyDiagnostics.Print("factory.''' + format_name + '''Export.error", "TFLEX_FACTORY_EXPORT_SOURCE_GRB is required");
      return 2;
    }
    if (String.IsNullOrWhiteSpace(target)) {
      EasyDiagnostics.Print("factory.''' + format_name + '''Export.error", "''' + env_target + ''' is required");
      return 3;
    }
    Document doc = null;
    using (var sess = EasySession.Start3D()) {
      try {
        doc = EasyPrototype.OpenCopy(source, visible: false);
        bool exported = EasyExport.''' + method + '''(doc, target);
        EasyDiagnostics.Print("factory.''' + format_name + '''Export.saved", exported);
        return exported ? 0 : 20;
      } finally {
        EasyPrototype.Close(doc);
      }
    }
  }
}
'''
    return run_csharp_snippet(
        code,
        mode="run",
        timeout_sec=timeout_sec,
        helpers=["easy_prototype", "easy_export"],
        environment={
            "TFLEX_FACTORY_EXPORT_SOURCE_GRB": str(source_grb),
            env_target: str(target),
        },
        artifact_prefix=f"factory_{format_name}_export",
        config=config,
    )


def _select_primary_grb(recipe_result: dict[str, Any]) -> Path | None:
    artifact_output = (recipe_result.get("recipe_artifacts") or {}).get("output_file")
    candidates: list[Path] = []
    if artifact_output:
        candidates.append(Path(str(artifact_output)))
    for artifact in recipe_result.get("artifacts") or []:
        path = artifact.get("path") if isinstance(artifact, dict) else None
        if path and str(path).lower().endswith(".grb"):
            candidates.append(Path(str(path)))
    existing = [path for path in candidates if path.exists() and path.is_file()]
    if not existing:
        return None
    saved = [path for path in existing if "saved" in path.stem.lower() or "output" in path.stem.lower()]
    return (saved or existing)[-1]


def _plan(recipe: str, args: dict[str, str], payload: dict[str, Any], *, selection: str, output: dict[str, Any]) -> dict[str, Any]:
    pending = _pending_operations(payload, selection)
    return {
        "ok": True,
        "recipe": recipe,
        "recipe_args": args,
        "selection": selection,
        "output": output["output"],
        "limitations": [
            "Phase 6 factory currently dispatches one verified recipe per payload run.",
            "Single-recipe plans execute one mutation group; multi-group payloads use generated visible C# when possible.",
            "GRB, STEP, PDF, DXF, and DWG output materialization are implemented in this phase.",
        ],
        "pending_operations": pending,
    }


def _pending_operations(payload: dict[str, Any], selected: str) -> list[str]:
    document = payload.get("document") or {}
    if not isinstance(document, dict):
        return []
    groups = [
        ("document.properties", document.get("properties")),
        ("document.variables", document.get("variables")),
        ("document.text_replacements", document.get("text_replacements")),
        ("document.tables", document.get("tables")),
    ]
    pending: list[str] = []
    for name, value in groups:
        if name == selected or selected.startswith(name + "."):
            continue
        if isinstance(value, dict) and value:
            pending.append(name)
        elif isinstance(value, list) and value:
            pending.append(name)
    return pending
