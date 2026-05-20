from tflex_harness.docs_search import DocsSearch


def test_search_symbols_finds_document_related_records():
    results = DocsSearch().search_symbols("TFlex Model Document", limit=10)
    assert results
    assert all(r["source"] == "symbols.jsonl" for r in results)
    assert any("TFlex" in (r.get("id") or "") for r in results)


def test_search_all_has_expected_scopes():
    result = DocsSearch().search("TFlexAPI", scope="all", limit=3)
    assert set(result) >= {"query", "symbols", "types", "chm"}
    assert result["symbols"]


def test_search_chm_returns_preview():
    result = DocsSearch().search_chm("T-FLEX", limit=3)
    assert result
    assert "preview" in result[0]
