"""
Billing tracker for per-tenant and per-model cost attribution.
"""

from collections import defaultdict
from ai_gateway.config.settings import get_settings
from ai_gateway.models.schemas import GatewayResponse, UsageReport
from ai_gateway.utils.logger import get_logger

logger = get_logger(__name__)


class BillingTracker:
    """Tracks token usage and costs per tenant and model."""

    def __init__(self) -> None:
        self._settings = get_settings()
        self._records: list[dict] = []
        self._tenant_usage: dict[str, dict] = defaultdict(lambda: {"requests": 0, "input_tokens": 0, "output_tokens": 0, "cost_usd": 0.0})

    def record(self, tenant_id: str, response: GatewayResponse) -> float:
        """
        Record usage and calculate cost.

        Args:
            tenant_id: Tenant to attribute cost to.
            response: The gateway response with token counts.

        Returns:
            Cost in USD for this request.
        """
        cost = self._calculate_cost(response.provider, response.input_tokens, response.output_tokens)
        response.cost_usd = cost

        self._records.append({"tenant_id": tenant_id, "provider": response.provider, "model": response.model, "input_tokens": response.input_tokens, "output_tokens": response.output_tokens, "cost_usd": cost})

        usage = self._tenant_usage[tenant_id]
        usage["requests"] += 1
        usage["input_tokens"] += response.input_tokens
        usage["output_tokens"] += response.output_tokens
        usage["cost_usd"] += cost

        return cost

    def get_tenant_report(self, tenant_id: str) -> UsageReport:
        """Get usage report for a tenant."""
        usage = self._tenant_usage.get(tenant_id, {"requests": 0, "input_tokens": 0, "output_tokens": 0, "cost_usd": 0.0})
        tenant_records = [r for r in self._records if r["tenant_id"] == tenant_id]

        # Group by provider
        by_provider: dict[str, dict] = defaultdict(lambda: {"requests": 0, "cost_usd": 0.0})
        by_model: dict[str, dict] = defaultdict(lambda: {"requests": 0, "cost_usd": 0.0})
        for r in tenant_records:
            by_provider[r["provider"]]["requests"] += 1
            by_provider[r["provider"]]["cost_usd"] += r["cost_usd"]
            by_model[r["model"]]["requests"] += 1
            by_model[r["model"]]["cost_usd"] += r["cost_usd"]

        return UsageReport(
            tenant_id=tenant_id, total_requests=usage["requests"],
            total_input_tokens=usage["input_tokens"], total_output_tokens=usage["output_tokens"],
            total_cost_usd=round(usage["cost_usd"], 6), by_provider=dict(by_provider), by_model=dict(by_model),
        )

    def _calculate_cost(self, provider: str, input_tokens: int, output_tokens: int) -> float:
        """Calculate cost based on provider pricing."""
        input_cost = self._settings.billing.cost_per_1k_input.get(provider, 0.005)
        output_cost = self._settings.billing.cost_per_1k_output.get(provider, 0.015)
        return round((input_tokens / 1000 * input_cost) + (output_tokens / 1000 * output_cost), 6)
