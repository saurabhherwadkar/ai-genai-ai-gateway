"""FastAPI router for the AI Gateway."""
from fastapi import APIRouter, HTTPException
from ai_gateway.routing import RequestRouter
from ai_gateway.ratelimit import RateLimiter
from ai_gateway.cache import ResponseCache
from ai_gateway.billing import BillingTracker
from ai_gateway.models.schemas import GatewayRequest, GatewayResponse
from ai_gateway.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/api/v1/gateway", tags=["gateway"])

_router = RequestRouter()
_limiter = RateLimiter()
_cache = ResponseCache()
_billing = BillingTracker()


@router.post("/generate", response_model=GatewayResponse)
async def generate(request: GatewayRequest) -> GatewayResponse:
    """Route a generation request through the gateway."""
    # Rate limit check
    if not _limiter.is_allowed(request.tenant_id):
        raise HTTPException(status_code=429, detail="Rate limit exceeded")

    # Cache check
    if request.cache_enabled:
        cached = _cache.get(request.prompt, request.system_message)
        if cached:
            cached.cached = True
            return cached

    # Route to provider
    try:
        response = await _router.route(request)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e)) from e

    # Track billing
    _billing.record(request.tenant_id, response)

    # Cache response
    if request.cache_enabled:
        _cache.put(request.prompt, request.system_message, response)

    return response


@router.get("/health")
async def health() -> dict:
    """Gateway health check with provider status."""
    provider_health = _router.get_health()
    return {
        "status": "healthy", "service": "ai-gateway",
        "providers": {name: h.model_dump() for name, h in provider_health.items()},
    }


@router.get("/ratelimit/{tenant_id}")
async def get_rate_limit(tenant_id: str) -> dict:
    """Get rate limit status for a tenant."""
    return _limiter.get_usage(tenant_id)


@router.get("/cache/stats")
async def cache_stats() -> dict:
    """Get cache statistics."""
    return _cache.get_stats()


@router.post("/cache/clear")
async def clear_cache() -> dict:
    """Clear the response cache."""
    _cache.clear()
    return {"cleared": True}


@router.get("/billing/{tenant_id}")
async def get_billing(tenant_id: str) -> dict:
    """Get billing report for a tenant."""
    return _billing.get_tenant_report(tenant_id).model_dump()
