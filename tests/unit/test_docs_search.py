import json

from tflex_harness.config import load_config
from tflex_harness.docs_search import DocsSearch
from tflex_harness.schemas import DOCS_SEARCH_MAX_LIMIT, normalize_limit


def test_docs_manifest_contains_expected_counts():
    cfg = load_config()
    assert cfg.manifest_json.exists()
    manifest = json.loads(cfg.manifest_json.read_text(encoding="utf-8"))
    assert manifest["symbol_count"] > 10000
    assert manifest["type_page_count"] > 1000
    assert manifest["chm_page_count"] > 10000
    assert set(manifest["assemblies"]) >= {
        "TFlexAPI",
        "TFlexAPI3D",
        "TFlexAPIData",
        "TFlexCommandAPI",
    }


def test_search_symbols_finds_document_related_records():
    results = DocsSearch().search_symbols("TFlex Model Document", limit=10)
    assert results
    assert all(r["source"] == "symbols.jsonl" for r in results)
    assert any("TFlex" in (r.get("id") or "") for r in results)


def test_search_all_has_expected_scopes():
    result = DocsSearch().search("TFlexAPI", scope="all", limit=3)
    assert set(result) >= {"query", "results", "symbols", "types", "chm"}
    assert result["scope"] == "all"
    assert result["limit"] == 3
    assert result["max_limit"] == DOCS_SEARCH_MAX_LIMIT
    assert result["results"]
    assert len(result["results"]) <= 3
    assert result["results"][0]["scope"] == "symbols"
    assert result["symbols"]


def test_search_symbols_scope_exposes_unified_results_contract():
    result = DocsSearch().search("Document SaveAs", scope="symbols", limit=1)
    assert result["scope"] == "symbols"
    assert result["limit"] == 1
    assert result["max_limit"] == DOCS_SEARCH_MAX_LIMIT
    assert result["results"]
    assert result["results"][0]["scope"] == "symbols"
    assert result["results"][0]["id"] == "M:TFlex.Model.Document.SaveAs(System.String)"
    assert result["symbols"][0]["id"] == result["results"][0]["id"]


def test_search_chm_returns_preview():
    result = DocsSearch().search_chm("T-FLEX", limit=3)
    assert result
    assert "preview" in result[0]


def test_docs_search_limits_are_bounded():
    assert normalize_limit(None) == 20
    assert normalize_limit(0) == 1
    assert normalize_limit(10_000) == DOCS_SEARCH_MAX_LIMIT

    result = DocsSearch().search("TFlex", scope="all", limit=10_000)
    assert result["limit"] == DOCS_SEARCH_MAX_LIMIT
    assert result["max_limit"] == DOCS_SEARCH_MAX_LIMIT
    assert len(result["results"]) <= DOCS_SEARCH_MAX_LIMIT
    assert len(result["symbols"]) <= DOCS_SEARCH_MAX_LIMIT
    assert len(result["types"]) <= DOCS_SEARCH_MAX_LIMIT
    assert len(result["chm"]) <= DOCS_SEARCH_MAX_LIMIT
