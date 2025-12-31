import pytest
from app import rate_limit

def test_rate_limit_blocks_after_quota(monkeypatch):
    # Freeze time
    t = 1000.0
    monkeypatch.setattr(rate_limit.time, "time", lambda: t)

    tenant = "tenant_a"

    # Allow MAX_REQUESTS
    for _ in range(rate_limit.MAX_REQUESTS):
        rate_limit.check_rate_limit(tenant)

    # Next should block
    with pytest.raises(RuntimeError):
        rate_limit.check_rate_limit(tenant)

def test_rate_limit_resets_after_window(monkeypatch):
    tenant = "tenant_b"
    t = 2000.0
    monkeypatch.setattr(rate_limit.time, "time", lambda: t)

    for _ in range(rate_limit.MAX_REQUESTS):
        rate_limit.check_rate_limit(tenant)

    # move time forward beyond window
    t += rate_limit.WINDOW_SECONDS + 1

    # should allow again
    rate_limit.check_rate_limit(tenant)
