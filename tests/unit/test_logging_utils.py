import json

from tflex_harness.config import HarnessConfig
from tflex_harness.logging_utils import append_jsonl, log_event, utc_timestamp


def _config(tmp_path):
    return HarnessConfig(
        repo_dir=tmp_path,
        docs_dir=tmp_path / "docs",
        tflex_install_dir=tmp_path / "tflex",
        tflex_program_dir=tmp_path / "tflex" / "Program",
        runner_dir=tmp_path / "runner" / "TFlexRunner",
        artifacts_dir=tmp_path / "artifacts",
        logs_dir=tmp_path / "logs",
    )


def test_utc_timestamp_is_iso_utc():
    assert utc_timestamp().endswith("Z")


def test_append_jsonl_writes_one_record_per_line(tmp_path):
    path = tmp_path / "logs" / "events.jsonl"

    append_jsonl(path, {"a": 1})
    append_jsonl(path, {"b": 2})

    lines = path.read_text(encoding="utf-8").splitlines()
    assert [json.loads(line) for line in lines] == [{"a": 1}, {"b": 2}]


def test_log_event_writes_standard_event_record(tmp_path):
    path = log_event("unit_test", {"ok": True}, config=_config(tmp_path))

    record = json.loads(path.read_text(encoding="utf-8").strip())
    assert record["event"] == "unit_test"
    assert record["payload"] == {"ok": True}
    assert record["timestamp"].endswith("Z")
