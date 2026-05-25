from __future__ import annotations

import argparse
import json
import sys

from .artifacts import json_default
from .diagnostics import get_environment
from .docs_search import DocsSearch
from .grb_reverse import write_semantic_outputs
from .prototypes import list_prototypes, prototype_info, scan_and_write_catalog
from .prototype_validation import validate_open_copy_save_batch
from .recipes import list_recipes, run_recipe
from .runner import run_csharp_snippet
from .schemas import DOCS_SEARCH_SCOPES, TFLEX_DOC_ASSEMBLIES
from .state import capture_tflex_state
from .workspace import save_snippet_candidate


def emit(data: object) -> None:
    print(json.dumps(data, ensure_ascii=False, indent=2, default=json_default))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="tflex-harness")
    sub = parser.add_subparsers(dest="command", required=True)

    env_p = sub.add_parser("env", help="Print environment diagnostics")

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

    state_p = sub.add_parser("state", help="Capture read-only live T-FLEX state")
    state_p.add_argument("--timeout-sec", type=int, default=60)

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

    args = parser.parse_args(argv)
    if args.command == "env":
        emit(get_environment())
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
    if args.command == "state":
        emit(capture_tflex_state(timeout_sec=args.timeout_sec))
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
    parser.error(f"unknown command {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
