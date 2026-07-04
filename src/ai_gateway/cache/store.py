"""
Response cache with TTL and LRU eviction.

Caches LLM responses by prompt hash to avoid redundant API calls
for identical or semantically similar requests.
"""

import hashlib
import time
from collections import OrderedDict

from ai_gateway.config.settings import get_settings
from ai_gateway.models.schemas import GatewayResponse
from ai_gateway.utils.logger import get_logger

logger = get_logger(__name__)


class ResponseCache:
    """LRU cache with TTL for gateway responses."""

    def __init__(self) -> None:
        self._settings = get_settings()
        self._cache: OrderedDict[str, tuple[float, GatewayResponse]] = OrderedDict()
        self._hits = 0
        self._misses = 0

    def get(self, prompt: str, system_message: str = "") -> GatewayResponse | None:
        """
        Look up a cached response.

        Args:
            prompt: The user prompt.
            system_message: System message for cache key.

        Returns:
            Cached GatewayResponse or None if not found/expired.
        """
        if not self._settings.cache.enabled:
            return None

        key = self._make_key(prompt, system_message)
        entry = self._cache.get(key)

        if entry is None:
            self._misses += 1
            return None

        timestamp, response = entry
        # Check TTL
        if time.time() - timestamp > self._settings.cache.ttl_seconds:
            del self._cache[key]
            self._misses += 1
            return None

        # Move to end (most recently used)
        self._cache.move_to_end(key)
        self._hits += 1
        logger.debug("cache_hit", key=key[:16])
        return response

    def put(self, prompt: str, system_message: str, response: GatewayResponse) -> None:
        """
        Store a response in the cache.

        Args:
            prompt: User prompt (for cache key).
            system_message: System message (for cache key).
            response: The response to cache.
        """
        if not self._settings.cache.enabled:
            return

        key = self._make_key(prompt, system_message)

        # Evict if at capacity
        while len(self._cache) >= self._settings.cache.max_entries:
            self._cache.popitem(last=False)  # Remove oldest

        self._cache[key] = (time.time(), response)

    def get_stats(self) -> dict:
        """Get cache statistics."""
        total = self._hits + self._misses
        hit_rate = self._hits / total if total > 0 else 0
        return {
            "entries": len(self._cache),
            "max_entries": self._settings.cache.max_entries,
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": round(hit_rate, 3),
        }

    def clear(self) -> None:
        """Clear the cache."""
        self._cache.clear()
        logger.info("cache_cleared")

    def _make_key(self, prompt: str, system_message: str) -> str:
        """Generate a cache key from prompt and system message."""
        content = f"{system_message}|{prompt}"
        return hashlib.sha256(content.encode()).hexdigest()
