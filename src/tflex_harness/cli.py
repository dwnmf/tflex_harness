from __future__ import annotations

import argparse
import json
import sys

from .artifacts import json_default
from .diagnostics import get_environment
from .docs_search import DocsSearch
from .runner import run_csharp_snippet


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

    args = parser.parse_args(argv)
    if args.command == "env":
        emit(get_environment())
        return 0
    if args.command == "search":
        emit(DocsSearch().search(args.query, scope=args.scope, assembly=args.assembly, limit=args.limit))
        return 0
    if args.command == "run-csharp":
        emit(run_csharp_snippet(args.code, mode=args.mode, timeout_sec=args.timeout_sec, references=args.references, artifact_prefix=args.artifact_prefix))
        return 0
    parser.error(f"unknown command {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
