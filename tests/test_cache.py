"""Tests for response cache."""
import pytest
from ai_gateway.cache.store import ResponseCache
from ai_gateway.models.schemas import GatewayResponse


@pytest.fixture
def cache() -> ResponseCache:
    return ResponseCache()


@pytest.fixture
def sample_response() -> GatewayResponse:
    return GatewayResponse(content="Hello!", provider="anthropic", model="claude-sonnet-4-20250514", input_tokens=10, output_tokens=5)


class TestResponseCache:
    def test_put_and_get(self, cache: ResponseCache, sample_response: GatewayResponse) -> None:
        cache.put("hello", "system", sample_response)
        result = cache.get("hello", "system")
        assert result is not None
        assert result.content == "Hello!"

    def test_cache_miss(self, cache: ResponseCache) -> None:
        result = cache.get("nonexistent", "")
        assert result is None

    def test_different_keys_no_collision(self, cache: ResponseCache, sample_response: GatewayResponse) -> None:
        cache.put("prompt_a", "sys", sample_response)
        assert cache.get("prompt_b", "sys") is None

    def test_stats_tracking(self, cache: ResponseCache, sample_response: GatewayResponse) -> None:
        cache.put("test", "", sample_response)
        cache.get("test", "")  # hit
        cache.get("other", "")  # miss
        stats = cache.get_stats()
        assert stats["hits"] == 1
        assert stats["misses"] == 1

    def test_clear(self, cache: ResponseCache, sample_response: GatewayResponse) -> None:
        cache.put("test", "", sample_response)
        cache.clear()
        assert cache.get("test", "") is None
