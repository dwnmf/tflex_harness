from __future__ import annotations

import argparse
import json
import sys

from .artifacts import json_default
from .bootstrap import bootstrap
from .diagnostics import get_environment, get_install_doctor
from .document_factory_batch import create_documents_from_payload_dir
from .document_factory import create_document_from_payload
from .document_factory_validation import validate_document_factory_samples
from .docs_search import DocsSearch
from .grb_reverse import write_semantic_outputs
from .mcp_config import MCP_CLIENTS, generate_mcp_config
from .prototype_metadata import capture_metadata_batch
from .prototypes import list_prototypes, prototype_info, scan_and_write_catalog
from .prototype_validation import (
    validate_electrical_labels_batch,
    validate_first_visible_text_batch,
    validate_open_copy_save_batch,
    validate_specification_bom_field_batch,
    validate_table_cell_batch,
    validate_title_mutation_batch,
)
from .recipes import list_recipes, new_helper_recipe, run_recipe
from .runner import run_csharp_snippet
from .schemas import DOCS_SEARCH_SCOPES, TFLEX_DOC_ASSEMBLIES
from .state import capture_tflex_state
from .ui_plugin import run_ui_plugin_probe
from .workspace import save_snippet_candidate


def emit(data: object) -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="replace")
    print(json.dumps(data, ensure_ascii=False, indent=2, default=json_default))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="tflex-harness")
    sub = parser.add_subparsers(dest="command", required=True)

    env_p = sub.add_parser("env", help="Print environment diagnostics")
    doctor_p = sub.add_parser("doctor", help="Print install readiness checks with fix hints")

    mcp_config_p = sub.add_parser("mcp-config", help="Print ready-to-copy MCP server config")
    mcp_config_p.add_argument("--for", choices=MCP_CLIENTS, default="codex", dest="client", help="MCP client config flavor")

    bootstrap_p = sub.add_parser("bootstrap", help="Clone docs, set env, and optionally register Codex skill")
    bootstrap_p.add_argument("--docs-dir", default=None, help="T-FLEX API docs checkout path; defaults to sibling tflex_api")
    bootstrap_p.add_argument("--docs-url", default=None, help="Docs git URL; defaults to dwnmf/tflex_api")
    bootstrap_p.add_argument("--full", action="store_true", help="Recommended first install: docs, persisted env, Codex skill, and checks")
    bootstrap_p.add_argument("--no-docs", action="store_true", help="Do not clone or update docs")
    bootstrap_p.add_argument("--update-docs", action="store_true", help="Run git pull --ff-only when docs repo already exists")
    bootstrap_p.add_argument("--persist-env", action="store_true", help="Persist TFLEX_HARNESS_REPO_DIR and TFLEX_API_DOCS_DIR with setx")
    bootstrap_p.add_argument("--register-codex-skill", action="store_true", help="Copy root SKILL.md into CODEX_HOME/.codex skills")
    bootstrap_p.add_argument("--symlink-skill", action="store_true", help="Prefer a symlink for Codex skill registration")
    bootstrap_p.add_argument("--no-checks", action="store_true", help="Skip docs completeness checks")

    search_p = sub.add_parser("search", help="Search T-FLEX API docs")
    search_p.add_argument("query")
    search_p.add_argument("--scope", choices=DOCS_SEARCH_SCOPES, default="all")
    search_p.add_argument("--assembly", choices=TFLEX_DOC_ASSEMBLIES, default=None)
    search_p.add_argument("--limit", type=int, default=10)

    run_p = sub.add_parser("run-csharp", help="Compile or run a C# snippet")
    run_p.add_argument("--code", required=True)
    run_p.add_argument("--mode", choices=["compile_only", "run"], default="run")
    run_p.add_argument("--timeout-sec", type=int, default=30)
    run_p.add_argument("--reference", action="append", choices=TFLEX_DOC_ASSEMBLIES, dest="references", default=None)
    run_p.add_argument("--helper", action="append", dest="helpers", default=None, help="C# helper set or helper source name to compile with the snippet")
    run_p.add_argument("--artifact-prefix", default="cli_snippet")
    run_p.add_argument("--env", action="append", default=[], help="Extra runtime environment variable in NAME=VALUE form")

    recipes_p = sub.add_parser("recipes", help="List verified recipes")

    recipe_p = sub.add_parser("run-recipe", help="Run a verified T-FLEX recipe")
    recipe_p.add_argument("name")
    recipe_p.add_argument("--arg", action="append", default=[], help="Recipe argument in NAME=VALUE form")
    recipe_p.add_argument("--timeout-sec", type=int, default=60)

    new_recipe_p = sub.add_parser("new-helper-recipe", help="Create a helper recipe scaffold")
    new_recipe_p.add_argument("name")
    new_recipe_p.add_argument("--helper", action="append", dest="helpers", default=None, help="Helper set or helper source to include")

    create_doc_p = sub.add_parser("create-document", help="Create a document from a JSON payload by dispatching a verified recipe")
    create_doc_p.add_argument("--payload", required=True, help="Path to document factory JSON payload")
    create_doc_p.add_argument("--timeout-sec", type=int, default=120)
    create_doc_p.add_argument("--dry-run", action="store_true")

    factory_samples_p = sub.add_parser("document-factory-samples", help="Run standard document factory sample payloads and write a matrix")
    factory_samples_p.add_argument("--timeout-sec", type=int, default=120)
    factory_samples_p.add_argument("--fail-fast", action="store_true")
    factory_samples_p.add_argument("--dry-run", action="store_true")
    factory_samples_p.add_argument("--output-dir", default=None)

    factory_batch_p = sub.add_parser("document-factory-batch", help="Run document factory payload JSON files from a folder or rerun failed rows from a matrix")
    factory_batch_p.add_argument("--payload-dir", default=None, help="Folder containing document factory payload JSON files")
    factory_batch_p.add_argument("--failed-matrix", default=None, help="Previous document_factory_batch_matrix.json; rerun rows where ok=false")
    factory_batch_p.add_argument("--audit-open-only", action="store_true", help="Open each payload prototype and collect metadata only; do not mutate, save, or export")
    factory_batch_p.add_argument("--glob", default="*.json", help="Payload filename glob; default: *.json")
    factory_batch_p.add_argument("--recursive", action="store_true")
    factory_batch_p.add_argument("--timeout-sec", type=int, default=120)
    factory_batch_p.add_argument("--fail-fast", action="store_true")
    factory_batch_p.add_argument("--dry-run", action="store_true")
    factory_batch_p.add_argument("--output-dir", default=None)

    state_p = sub.add_parser("state", help="Capture read-only live T-FLEX state")
    state_p.add_argument("--timeout-sec", type=int, default=60)

    ui_probe_p = sub.add_parser("ui-plugin-probe", help="Build and live-probe a minimal T-FLEX UI plugin registration path")
    ui_probe_p.add_argument("--timeout-sec", type=int, default=90)
    ui_probe_p.add_argument("--startup-wait-sec", type=int, default=10)
    ui_probe_p.add_argument("--compile-only", action="store_true")

    save_p = sub.add_parser("save-snippet", help="Save a C# snippet candidate under agent_workspace/snippets")
    save_p.add_argument("name")
    save_p.add_argument("--code", required=True)
    save_p.add_argument("--markdown", default=None)

    reverse_p = sub.add_parser("reverse-evidence", help="Recognize GRB contour evidence and emit parametric C#")
    reverse_p.add_argument("evidence_json")
    reverse_p.add_argument("--output-dir", required=True)

    proto_scan_p = sub.add_parser("prototypes-scan", help="Scan installed T-FLEX prototype corpus")
    proto_scan_p.add_argument("--root", default=None, help="Prototype root override; defaults to TFLEX_PROTOTYPES_DIR or T-FLEX Program\\Прототипы")
    proto_scan_p.add_argument("--output-dir", default=None, help="Where to write catalog.json; defaults to artifacts/prototype_catalog/<stamp>")

    proto_list_p = sub.add_parser("prototypes-list", help="List indexed T-FLEX prototypes")
    proto_list_p.add_argument("--root", default=None)
    proto_list_p.add_argument("--category", default=None)
    proto_list_p.add_argument("--extension", default=".grb", help="Filter extension; use empty string for all supported files")
    proto_list_p.add_argument("--limit", type=int, default=None)

    proto_info_p = sub.add_parser("prototypes-info", help="Show one prototype by id, relative path, absolute path, or name")
    proto_info_p.add_argument("selector")
    proto_info_p.add_argument("--root", default=None)

    proto_batch_p = sub.add_parser("prototypes-open-save-batch", help="Batch copy/open/save .grb prototypes and write validation matrix")
    proto_batch_p.add_argument("--root", default=None)
    proto_batch_p.add_argument("--category", default=None)
    proto_batch_p.add_argument("--limit", type=int, default=None)
    proto_batch_p.add_argument("--timeout-sec", type=int, default=120)
    proto_batch_p.add_argument("--fail-fast", action="store_true")
    proto_batch_p.add_argument("--dry-run", action="store_true")
    proto_batch_p.add_argument("--output-dir", default=None)

    proto_title_p = sub.add_parser("prototypes-title-batch", help="Batch set Document.Properties.Title on copied .grb prototypes and write validation matrix")
    proto_title_p.add_argument("--root", default=None)
    proto_title_p.add_argument("--category", default=None)
    proto_title_p.add_argument("--limit", type=int, default=None)
    proto_title_p.add_argument("--timeout-sec", type=int, default=120)
    proto_title_p.add_argument("--fail-fast", action="store_true")
    proto_title_p.add_argument("--dry-run", action="store_true")
    proto_title_p.add_argument("--output-dir", default=None)
    proto_title_p.add_argument("--property-name", default="Title")
    proto_title_p.add_argument("--value-prefix", default="Harness Title Matrix")

    proto_table_p = sub.add_parser("prototypes-table-cell-batch", help="Batch set one RichText table cell on copied .grb prototypes and write validation matrix")
    proto_table_p.add_argument("--root", default=None)
    proto_table_p.add_argument("--category", default=None)
    proto_table_p.add_argument("--limit", type=int, default=None)
    proto_table_p.add_argument("--timeout-sec", type=int, default=120)
    proto_table_p.add_argument("--fail-fast", action="store_true")
    proto_table_p.add_argument("--dry-run", action="store_true")
    proto_table_p.add_argument("--output-dir", default=None)
    proto_table_p.add_argument("--cell-index", type=int, default=2)
    proto_table_p.add_argument("--value-prefix", default="Harness Table Matrix")

    proto_visible_p = sub.add_parser("prototypes-first-visible-text-batch", help="Batch replace first visible non-table text on copied .grb prototypes and write validation matrix")
    proto_visible_p.add_argument("--root", default=None)
    proto_visible_p.add_argument("--category", default=None)
    proto_visible_p.add_argument("--limit", type=int, default=None)
    proto_visible_p.add_argument("--timeout-sec", type=int, default=120)
    proto_visible_p.add_argument("--fail-fast", action="store_true")
    proto_visible_p.add_argument("--dry-run", action="store_true")
    proto_visible_p.add_argument("--output-dir", default=None)
    proto_visible_p.add_argument("--value-prefix", default="Harness Visible Text Matrix")

    proto_electrical_p = sub.add_parser("prototypes-electrical-labels-batch", help="Batch mutate electrical labels via visible text first, then text-variable fallback, and write classification matrix")
    proto_electrical_p.add_argument("--root", default=None)
    proto_electrical_p.add_argument("--category", default="Электротехника")
    proto_electrical_p.add_argument("--limit", type=int, default=None)
    proto_electrical_p.add_argument("--timeout-sec", type=int, default=120)
    proto_electrical_p.add_argument("--fail-fast", action="store_true")
    proto_electrical_p.add_argument("--dry-run", action="store_true")
    proto_electrical_p.add_argument("--output-dir", default=None)
    proto_electrical_p.add_argument("--variable-name", default="$Наименование")
    proto_electrical_p.add_argument("--value-prefix", default="Harness Electrical Label Matrix")

    proto_spec_bom_p = sub.add_parser("prototypes-specification-bom-field-batch", help="Batch set one BOMObject standard field on copied specification .grb prototypes and write validation matrix")
    proto_spec_bom_p.add_argument("--root", default=None)
    proto_spec_bom_p.add_argument("--category", default="Спецификации")
    proto_spec_bom_p.add_argument("--limit", type=int, default=None)
    proto_spec_bom_p.add_argument("--timeout-sec", type=int, default=120)
    proto_spec_bom_p.add_argument("--fail-fast", action="store_true")
    proto_spec_bom_p.add_argument("--dry-run", action="store_true")
    proto_spec_bom_p.add_argument("--output-dir", default=None)
    proto_spec_bom_p.add_argument("--standard-field", default="Desc")
    proto_spec_bom_p.add_argument("--add-record", action="store_true", default=True)
    proto_spec_bom_p.add_argument("--no-add-record", dest="add_record", action="store_false")
    proto_spec_bom_p.add_argument("--value-prefix", default="Harness Spec BOM Matrix")

    proto_meta_p = sub.add_parser("prototypes-metadata", help="Extract metadata from copied .grb prototypes and write JSON/CSV indexes")
    proto_meta_p.add_argument("--root", default=None)
    proto_meta_p.add_argument("--category", default=None)
    proto_meta_p.add_argument("--limit", type=int, default=None)
    proto_meta_p.add_argument("--timeout-sec", type=int, default=120)
    proto_meta_p.add_argument("--output-dir", default=None)

    args = parser.parse_args(argv)
    if args.command == "env":
        emit(get_environment())
        return 0
    if args.command == "doctor":
        emit(get_install_doctor())
        return 0
    if args.command == "mcp-config":
        emit(generate_mcp_config(args.client))
        return 0
    if args.command == "bootstrap":
        emit(
            bootstrap(
                docs_dir=args.docs_dir,
                docs_url=args.docs_url or "https://github.com/dwnmf/tflex_api",
                full=args.full,
                no_docs=args.no_docs,
                update_docs=args.update_docs,
                persist_env=args.persist_env,
                register_codex_skill=args.register_codex_skill,
                symlink_skill=args.symlink_skill,
                no_checks=args.no_checks,
            )
        )
        return 0
    if args.command == "search":
        emit(DocsSearch().search(args.query, scope=args.scope, assembly=args.assembly, limit=args.limit))
        return 0
    if args.command == "run-csharp":
        extra_env = {}
        for item in args.env:
            if "=" not in item:
                parser.error(f"--env must be NAME=VALUE, got {item!r}")
            key, value = item.split("=", 1)
            extra_env[key] = value
        emit(run_csharp_snippet(args.code, mode=args.mode, timeout_sec=args.timeout_sec, references=args.references, helpers=args.helpers, artifact_prefix=args.artifact_prefix, environment=extra_env))
        return 0
    if args.command == "recipes":
        emit({"recipes": list_recipes()})
        return 0
    if args.command == "run-recipe":
        recipe_args = {}
        for item in args.arg:
            if "=" not in item:
                parser.error(f"--arg must be NAME=VALUE, got {item!r}")
            key, value = item.split("=", 1)
            recipe_args[key] = value
        emit(run_recipe(args.name, args=recipe_args, timeout_sec=args.timeout_sec))
        return 0
    if args.command == "new-helper-recipe":
        emit(new_helper_recipe(args.name, helpers=args.helpers))
        return 0
    if args.command == "create-document":
        emit(create_document_from_payload(args.payload, timeout_sec=args.timeout_sec, dry_run=args.dry_run))
        return 0
    if args.command == "document-factory-samples":
        emit(validate_document_factory_samples(timeout_sec=args.timeout_sec, dry_run=args.dry_run, fail_fast=args.fail_fast, output_dir=args.output_dir))
        return 0
    if args.command == "document-factory-batch":
        emit(
            create_documents_from_payload_dir(
                args.payload_dir,
                pattern=args.glob,
                recursive=args.recursive,
                failed_matrix=args.failed_matrix,
                audit_open_only=args.audit_open_only,
                timeout_sec=args.timeout_sec,
                dry_run=args.dry_run,
                fail_fast=args.fail_fast,
                output_dir=args.output_dir,
            )
        )
        return 0
    if args.command == "state":
        emit(capture_tflex_state(timeout_sec=args.timeout_sec))
        return 0
    if args.command == "ui-plugin-probe":
        emit(run_ui_plugin_probe(timeout_sec=args.timeout_sec, startup_wait_sec=args.startup_wait_sec, compile_only=args.compile_only))
        return 0
    if args.command == "save-snippet":
        emit(save_snippet_candidate(args.name, code=args.code, markdown=args.markdown))
        return 0
    if args.command == "reverse-evidence":
        emit(write_semantic_outputs(args.evidence_json, args.output_dir))
        return 0
    if args.command == "prototypes-scan":
        emit(scan_and_write_catalog(root=args.root, output_dir=args.output_dir))
        return 0
    if args.command == "prototypes-list":
        extension = args.extension if args.extension else None
        emit(list_prototypes(root=args.root, category=args.category, extension=extension, limit=args.limit))
        return 0
    if args.command == "prototypes-info":
        emit(prototype_info(args.selector, root=args.root))
        return 0
    if args.command == "prototypes-open-save-batch":
        emit(validate_open_copy_save_batch(root=args.root, category=args.category, limit=args.limit, timeout_sec=args.timeout_sec, fail_fast=args.fail_fast, dry_run=args.dry_run, output_dir=args.output_dir))
        return 0
    if args.command == "prototypes-title-batch":
        emit(validate_title_mutation_batch(root=args.root, category=args.category, limit=args.limit, timeout_sec=args.timeout_sec, fail_fast=args.fail_fast, dry_run=args.dry_run, output_dir=args.output_dir, property_name=args.property_name, value_prefix=args.value_prefix))
        return 0
    if args.command == "prototypes-table-cell-batch":
        emit(validate_table_cell_batch(root=args.root, category=args.category, limit=args.limit, timeout_sec=args.timeout_sec, fail_fast=args.fail_fast, dry_run=args.dry_run, output_dir=args.output_dir, cell_index=args.cell_index, value_prefix=args.value_prefix))
        return 0
    if args.command == "prototypes-first-visible-text-batch":
        emit(validate_first_visible_text_batch(root=args.root, category=args.category, limit=args.limit, timeout_sec=args.timeout_sec, fail_fast=args.fail_fast, dry_run=args.dry_run, output_dir=args.output_dir, value_prefix=args.value_prefix))
        return 0
    if args.command == "prototypes-electrical-labels-batch":
        emit(validate_electrical_labels_batch(root=args.root, category=args.category, limit=args.limit, timeout_sec=args.timeout_sec, fail_fast=args.fail_fast, dry_run=args.dry_run, output_dir=args.output_dir, variable_name=args.variable_name, value_prefix=args.value_prefix))
        return 0
    if args.command == "prototypes-specification-bom-field-batch":
        emit(validate_specification_bom_field_batch(root=args.root, category=args.category, limit=args.limit, timeout_sec=args.timeout_sec, fail_fast=args.fail_fast, dry_run=args.dry_run, output_dir=args.output_dir, standard_field=args.standard_field, add_record=args.add_record, value_prefix=args.value_prefix))
        return 0
    if args.command == "prototypes-metadata":
        emit(capture_metadata_batch(root=args.root, category=args.category, limit=args.limit, timeout_sec=args.timeout_sec, output_dir=args.output_dir))
        return 0
    parser.error(f"unknown command {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
