"""Pydantic schemas for the AI Gateway."""
from datetime import datetime
from pydantic import BaseModel, Field


class GatewayRequest(BaseModel):
    """Request routed through the gateway."""
    prompt: str = Field(description="User prompt")
    system_message: str = Field(default="You are a helpful assistant.")
    model: str | None = Field(default=None, description="Model override")
    provider: str | None = Field(default=None, description="Provider override")
    temperature: float = Field(default=0.7)
    max_tokens: int = Field(default=4096)
    tenant_id: str = Field(default="default")
    cache_enabled: bool = Field(default=True)


class GatewayResponse(BaseModel):
    """Response from the gateway."""
    content: str = Field(description="Generated content")
    provider: str = Field(description="Provider that served the request")
    model: str = Field(description="Model used")
    input_tokens: int = Field(default=0)
    output_tokens: int = Field(default=0)
    latency_ms: float = Field(default=0.0)
    cost_usd: float = Field(default=0.0)
    cached: bool = Field(default=False)
    fallback_used: bool = Field(default=False)


class ProviderHealth(BaseModel):
    """Health status of a provider."""
    provider: str = Field(description="Provider name")
    healthy: bool = Field(default=True)
    latency_ms: float = Field(default=0.0)
    error_rate: float = Field(default=0.0)
    last_check: datetime | None = Field(default=None)


class UsageReport(BaseModel):
    """Usage report for a tenant."""
    tenant_id: str = Field(description="Tenant ID")
    total_requests: int = Field(default=0)
    total_input_tokens: int = Field(default=0)
    total_output_tokens: int = Field(default=0)
    total_cost_usd: float = Field(default=0.0)
    by_provider: dict[str, dict] = Field(default_factory=dict)
    by_model: dict[str, dict] = Field(default_factory=dict)
