"""Anthropic Claude provider adapter."""
import anthropic
from ai_gateway.config.settings import get_settings
from ai_gateway.models.schemas import GatewayRequest, GatewayResponse
from ai_gateway.utils.logger import get_logger

logger = get_logger(__name__)


class AnthropicProvider:
    """Anthropic Claude API provider."""

    def __init__(self) -> None:
        settings = get_settings()
        self._client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key, timeout=60)
        self.name = "anthropic"
        self.default_model = "claude-sonnet-4-20250514"

    async def generate(self, request: GatewayRequest) -> GatewayResponse:
        """Generate a response using Claude."""
        model = request.model or self.default_model
        message = await self._client.messages.create(
            model=model, max_tokens=request.max_tokens, temperature=request.temperature,
            system=request.system_message, messages=[{"role": "user", "content": request.prompt}],
        )
        content = message.content[0].text if message.content else ""
        return GatewayResponse(
            content=content, provider=self.name, model=model,
            input_tokens=message.usage.input_tokens, output_tokens=message.usage.output_tokens,
        )

    async def health_check(self) -> bool:
        """Check if the provider is healthy."""
        try:
            await self._client.messages.create(
                model=self.default_model, max_tokens=10, messages=[{"role": "user", "content": "hi"}],
            )
            return True
        except Exception:
            return False
