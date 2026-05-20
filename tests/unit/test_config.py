from tflex_harness.config import load_config


def test_config_defaults_point_to_existing_docs():
    cfg = load_config()
    assert cfg.docs_dir.exists()
    assert cfg.symbols_jsonl.exists()
    assert cfg.chm_pages_jsonl.exists()
    assert cfg.types_dir.exists()
