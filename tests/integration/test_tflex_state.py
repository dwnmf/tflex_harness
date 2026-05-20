import pytest

from tflex_harness.state import capture_tflex_state


@pytest.mark.integration
def test_capture_tflex_state_live_readonly():
    state = capture_tflex_state(timeout_sec=60)
    assert state["ok"] is True, state
    assert state["session_initialized"] is True
    assert isinstance(state["document_count"], int)
    assert isinstance(state["documents"], list)
    assert "session=False" in state["run"]["stdout"]
