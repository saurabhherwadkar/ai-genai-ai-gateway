"""
Request router with priority-based selection and automatic fallback.

Routes requests to providers based on priority, health status, and
load, with automatic fallback on failure.
"""

import time

from ai_gateway.config.settings import get_settings
from ai_gateway.models.schemas import GatewayRequest, GatewayResponse, ProviderHealth
from ai_gateway.providers.anthropic_provider import AnthropicProvider
from ai_gateway.providers.openai_provider import OpenAIProvider
from ai_gateway.utils.logger import get_logger

logger = get_logger(__name__)


class RequestRouter:
    """
    Routes requests across providers with fallback and retry.

    Selects providers by priority, falls back on failure, and
    tracks provider health for intelligent routing.
    """

    def __init__(self) -> None:
        self._settings = get_settings()
        self._providers = {
            "anthropic": AnthropicProvider(),
            "openai": OpenAIProvider(),
        }
        self._health: dict[str, ProviderHealth] = {
            name: ProviderHealth(provider=name) for name in self._providers
        }
        # Priority order (lower = higher priority)
        self._priority = ["anthropic", "openai"]

    async def route(self, request: GatewayRequest) -> GatewayResponse:
        """
        Route a request to the best available provider.

        Args:
            request: The gateway request to route.

        Returns:
            GatewayResponse from the selected provider.

        Raises:
            RuntimeError: If all providers fail.
        """
        # If specific provider requested, try it first
        if request.provider and request.provider in self._providers:
            providers_to_try = [request.provider]
            if self._settings.routing.fallback_enabled:
                providers_to_try += [p for p in self._priority if p != request.provider]
        else:
            providers_to_try = [p for p in self._priority if self._health[p].healthy]
            if not providers_to_try:
                providers_to_try = self._priority  # Try all if none marked healthy

        # Try each provider with retries
        last_error = None
        for provider_name in providers_to_try:
            provider = self._providers[provider_name]
            for attempt in range(self._settings.routing.max_retries + 1):
                try:
                    start = time.time()
                    response = await provider.generate(request)
                    latency = (time.time() - start) * 1000
                    response.latency_ms = round(latency, 2)
                    response.fallback_used = provider_name != providers_to_try[0]

                    # Update health
                    self._health[provider_name].healthy = True
                    self._health[provider_name].latency_ms = latency

                    logger.info("request_routed", provider=provider_name, latency_ms=latency)
                    return response

                except Exception as e:
                    last_error = e
                    logger.warning("provider_attempt_failed", provider=provider_name, attempt=attempt + 1, error=str(e))
                    self._health[provider_name].healthy = False

        raise RuntimeError(f"All providers failed. Last error: {last_error}")

    def get_health(self) -> dict[str, ProviderHealth]:
        """Get health status of all providers."""
        return self._health
