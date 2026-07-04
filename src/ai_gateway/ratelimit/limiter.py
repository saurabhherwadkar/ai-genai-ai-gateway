"""
Sliding window rate limiter with per-tenant support.
"""

import time
from collections import defaultdict, deque

from ai_gateway.config.settings import get_settings
from ai_gateway.utils.logger import get_logger

logger = get_logger(__name__)


class RateLimiter:
    """Per-tenant sliding window rate limiter."""

    def __init__(self) -> None:
        self._settings = get_settings()
        self._request_windows: dict[str, deque] = defaultdict(deque)
        self._tenant_limits: dict[str, int] = {}

    def set_tenant_limit(self, tenant_id: str, rpm: int) -> None:
        """Set custom rate limit for a tenant."""
        self._tenant_limits[tenant_id] = rpm

    def is_allowed(self, tenant_id: str = "default") -> bool:
        """
        Check if a request from this tenant is within rate limits.

        Args:
            tenant_id: Tenant identifier.

        Returns:
            True if the request should be allowed.
        """
        if not self._settings.ratelimit.enabled:
            return True

        now = time.time()
        window = self._request_windows[tenant_id]

        # Remove entries older than 60s
        while window and window[0] < now - 60:
            window.popleft()

        # Get limit for this tenant
        limit = self._tenant_limits.get(tenant_id, self._settings.ratelimit.default_rpm)

        if len(window) >= limit:
            logger.warning("rate_limited", tenant=tenant_id, current=len(window), limit=limit)
            return False

        window.append(now)
        return True

    def get_usage(self, tenant_id: str) -> dict:
        """Get current rate limit usage for a tenant."""
        now = time.time()
        window = self._request_windows.get(tenant_id, deque())
        # Count requests in current window
        current = sum(1 for t in window if now - t < 60)
        limit = self._tenant_limits.get(tenant_id, self._settings.ratelimit.default_rpm)
        return {"tenant_id": tenant_id, "current_rpm": current, "limit_rpm": limit, "remaining": max(0, limit - current)}
