import pytest

from tflex_harness.diagnostics import get_environment, get_live_environment_blockers


@pytest.fixture(scope="session", autouse=True)
def require_live_tflex_environment():
    environment = get_environment()
    blockers = get_live_environment_blockers(environment)
    if blockers:
        pytest.skip("T-FLEX live environment unavailable: " + "; ".join(blockers))
