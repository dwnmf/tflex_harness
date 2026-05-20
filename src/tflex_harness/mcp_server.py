from __future__ import annotations

from .diagnostics import get_environment
from .docs_search import DocsSearch
from .runner import run_csharp_snippet


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
    def run_csharp_tflex(code: str, mode: str = "run", timeout_sec: int = 30, references: list[str] | None = None, artifact_prefix: str = "mcp_snippet") -> dict:
        """Compile or run a visible C# snippet against local T-FLEX API references."""
        return run_csharp_snippet(code=code, mode=mode, timeout_sec=timeout_sec, references=references, artifact_prefix=artifact_prefix)

    return server


def main() -> None:  # pragma: no cover - manual entrypoint
    create_server().run()


if __name__ == "__main__":
    main()
