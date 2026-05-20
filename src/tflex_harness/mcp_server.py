from __future__ import annotations

from .diagnostics import get_environment
from .docs_search import DocsSearch
from .recipes import list_recipes, run_recipe
from .runner import run_csharp_snippet
from .state import capture_tflex_state as capture_tflex_state_impl


def create_server():
    """Create an MCP server when the optional `mcp` package is installed."""
    try:
        from mcp.server.fastmcp import FastMCP
    except Exception as exc:  # pragma: no cover - depends on optional dependency
        raise RuntimeError("Install optional dependency with `pip install -e .[mcp]` to run the MCP server") from exc

    server = FastMCP("tflex-harness")
    docs = DocsSearch()

    @server.tool()
    def search_tflex_docs(query: str, scope: str = "all", assembly: str | None = None, limit: int = 20) -> dict:
        """Search T-FLEX CAD 17 API docs in symbols/type pages/CHM JSONL."""
        return docs.search(query=query, scope=scope, assembly=assembly, limit=limit)

    @server.tool()
    def get_tflex_environment() -> dict:
        """Return local T-FLEX/docs/compiler environment diagnostics."""
        return get_environment()

    @server.tool()
    def run_csharp_tflex(code: str, mode: str = "run", timeout_sec: int = 30, references: list[str] | None = None, artifact_prefix: str = "mcp_snippet", environment: dict[str, str] | None = None) -> dict:
        """Compile or run a visible C# snippet against local T-FLEX API references."""
        return run_csharp_snippet(code=code, mode=mode, timeout_sec=timeout_sec, references=references, artifact_prefix=artifact_prefix, environment=environment)

    @server.tool()
    def list_tflex_recipes() -> dict:
        """List verified T-FLEX recipes available through the harness."""
        return {"recipes": list_recipes()}

    @server.tool()
    def run_tflex_recipe(recipe: str, args: dict | None = None, timeout_sec: int = 60) -> dict:
        """Run a verified T-FLEX recipe by name with JSON args."""
        return run_recipe(name=recipe, args=args or {}, timeout_sec=timeout_sec)

    @server.tool()
    def capture_tflex_state(timeout_sec: int = 60) -> dict:
        """Capture read-only live T-FLEX session/document state via a short C# probe."""
        return capture_tflex_state_impl(timeout_sec=timeout_sec)

    return server


def main() -> None:  # pragma: no cover - manual entrypoint
    create_server().run()


if __name__ == "__main__":
    main()
