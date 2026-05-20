from __future__ import annotations

import argparse
import json
import sys

from .artifacts import json_default
from .diagnostics import get_environment
from .docs_search import DocsSearch
from .recipes import list_recipes, run_recipe
from .runner import run_csharp_snippet
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
    search_p.add_argument("--scope", choices=["symbols", "types", "chm", "all"], default="all")
    search_p.add_argument("--assembly", default=None)
    search_p.add_argument("--limit", type=int, default=10)

    run_p = sub.add_parser("run-csharp", help="Compile or run a C# snippet")
    run_p.add_argument("--code", required=True)
    run_p.add_argument("--mode", choices=["compile_only", "run"], default="run")
    run_p.add_argument("--timeout-sec", type=int, default=30)
    run_p.add_argument("--reference", action="append", dest="references", default=None)
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
        emit(run_csharp_snippet(args.code, mode=args.mode, timeout_sec=args.timeout_sec, references=args.references, artifact_prefix=args.artifact_prefix, environment=extra_env))
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
    parser.error(f"unknown command {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
