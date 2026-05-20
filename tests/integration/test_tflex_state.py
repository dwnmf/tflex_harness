import pytest

from tflex_harness.state import capture_tflex_state


@pytest.mark.integration
def test_capture_tflex_state_live_readonly():
    state = capture_tflex_state(timeout_sec=60)
    assert state["ok"] is True, state
    assert state["session_initialized"] is True
    assert isinstance(state["document_count"], int)
    assert isinstance(state["documents"], list)
    assert isinstance(state["object_counts"], dict)
    assert state["object_counts"]["documents"] == state["document_count"]
    assert isinstance(state["selection"], list)
    assert isinstance(state["artifacts"], list)
    assert isinstance(state["object2d_types"], dict)
    assert isinstance(state["operation3d_types"], dict)
    assert isinstance(state["operations3d"], list)
    assert "session=False" in state["run"]["stdout"]
