from __future__ import annotations

from typing import Literal

from .diagnostics import get_environment
from .document_factory import create_document_from_payload
from .document_factory_batch import create_documents_from_payload_dir
from .docs_search import DocsSearch
from .recipes import list_recipes, run_recipe
from .runner import run_csharp_snippet
from .state import capture_tflex_state as capture_tflex_state_impl
from .workspace import save_snippet_candidate


def create_server():
    """Create an MCP server when the optional `mcp` package is installed."""
    try:
        from mcp.server.fastmcp import FastMCP
    except Exception as exc:  # pragma: no cover - depends on optional dependency
        raise RuntimeError("Install optional dependency with `pip install -e .[mcp]` to run the MCP server") from exc

    server = FastMCP("tflex-harness")
    docs = DocsSearch()

    @server.tool()
    def search_tflex_docs(query: str, scope: Literal["symbols", "types", "chm", "all"] = "all", assembly: Literal["TFlexAPI", "TFlexAPI3D", "TFlexAPIData", "TFlexCommandAPI"] | None = None, limit: int = 20) -> dict:
        """Search T-FLEX CAD 17 API docs in symbols/type pages/CHM JSONL."""
        return docs.search(query=query, scope=scope, assembly=assembly, limit=limit)

    @server.tool()
    def get_tflex_environment() -> dict:
        """Return local T-FLEX/docs/compiler environment diagnostics."""
        return get_environment()

    @server.tool()
    def run_csharp_tflex(code: str, mode: Literal["compile_only", "run"] = "run", timeout_sec: int = 30, references: list[Literal["TFlexAPI", "TFlexAPI3D", "TFlexAPIData", "TFlexCommandAPI"]] | None = None, helpers: list[str] | None = None, artifact_prefix: str = "mcp_snippet", environment: dict[str, str] | None = None) -> dict:
        """Compile or run a visible C# snippet against local T-FLEX API references."""
        return run_csharp_snippet(code=code, mode=mode, timeout_sec=timeout_sec, references=references, helpers=helpers, artifact_prefix=artifact_prefix, environment=environment)

    @server.tool()
    def list_tflex_recipes() -> dict:
        """List verified T-FLEX recipes available through the harness."""
        return {"recipes": list_recipes()}

    @server.tool()
    def run_tflex_recipe(recipe: str, args: dict | None = None, timeout_sec: int = 60) -> dict:
        """Run a verified T-FLEX recipe by name with JSON args."""
        return run_recipe(name=recipe, args=args or {}, timeout_sec=timeout_sec)

    @server.tool()
    def create_tflex_document(payload_path: str, timeout_sec: int = 120, dry_run: bool = False) -> dict:
        """Create or dry-run one T-FLEX document factory payload JSON file."""
        return create_document_from_payload(payload_path, timeout_sec=timeout_sec, dry_run=dry_run)

    @server.tool()
    def run_tflex_document_factory_batch(payload_dir: str | None = None, pattern: str = "*.json", recursive: bool = False, failed_matrix: str | None = None, audit_open_only: bool = False, timeout_sec: int = 120, dry_run: bool = False, fail_fast: bool = False, output_dir: str | None = None) -> dict:
        """Run or dry-run document factory payload JSON files from a folder, or rerun failed rows from a previous matrix."""
        return create_documents_from_payload_dir(
            payload_dir,
            pattern=pattern,
            recursive=recursive,
            failed_matrix=failed_matrix,
            audit_open_only=audit_open_only,
            timeout_sec=timeout_sec,
            dry_run=dry_run,
            fail_fast=fail_fast,
            output_dir=output_dir,
        )

    @server.tool()
    def capture_tflex_state(timeout_sec: int = 60) -> dict:
        """Capture read-only live T-FLEX session/document state via a short C# probe."""
        return capture_tflex_state_impl(timeout_sec=timeout_sec)

    @server.tool()
    def save_tflex_snippet_candidate(name: str, code: str, markdown: str | None = None, metadata: dict | None = None) -> dict:
        """Save a visible C# snippet candidate for later live verification and recipe promotion."""
        return save_snippet_candidate(name=name, code=code, markdown=markdown, metadata=metadata or {})

    return server


def main() -> None:  # pragma: no cover - manual entrypoint
    create_server().run()


if __name__ == "__main__":
    main()
