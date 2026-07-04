"""Tests for rate limiter."""
import pytest
from ai_gateway.ratelimit.limiter import RateLimiter


@pytest.fixture
def limiter() -> RateLimiter:
    return RateLimiter()


class TestRateLimiter:
    def test_allows_within_limit(self, limiter: RateLimiter) -> None:
        for _ in range(10):
            assert limiter.is_allowed("tenant-1") is True

    def test_per_tenant_isolation(self, limiter: RateLimiter) -> None:
        # Exhaust tenant-1
        limiter.set_tenant_limit("tenant-1", 2)
        assert limiter.is_allowed("tenant-1") is True
        assert limiter.is_allowed("tenant-1") is True
        assert limiter.is_allowed("tenant-1") is False
        # tenant-2 still works
        assert limiter.is_allowed("tenant-2") is True

    def test_get_usage(self, limiter: RateLimiter) -> None:
        limiter.is_allowed("t1")
        limiter.is_allowed("t1")
        usage = limiter.get_usage("t1")
        assert usage["current_rpm"] == 2
        assert usage["remaining"] > 0
