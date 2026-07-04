"""OpenAI GPT provider adapter."""
import openai
from ai_gateway.config.settings import get_settings
from ai_gateway.models.schemas import GatewayRequest, GatewayResponse
from ai_gateway.utils.logger import get_logger

logger = get_logger(__name__)


class OpenAIProvider:
    """OpenAI API provider."""

    def __init__(self) -> None:
        settings = get_settings()
        self._client = openai.AsyncOpenAI(api_key=settings.openai_api_key, timeout=60)
        self.name = "openai"
        self.default_model = "gpt-4o"

    async def generate(self, request: GatewayRequest) -> GatewayResponse:
        """Generate a response using GPT."""
        model = request.model or self.default_model
        completion = await self._client.chat.completions.create(
            model=model, max_tokens=request.max_tokens, temperature=request.temperature,
            messages=[{"role": "system", "content": request.system_message}, {"role": "user", "content": request.prompt}],
        )
        content = completion.choices[0].message.content if completion.choices else ""
        input_tokens = completion.usage.prompt_tokens if completion.usage else 0
        output_tokens = completion.usage.completion_tokens if completion.usage else 0
        return GatewayResponse(
            content=content, provider=self.name, model=model,
            input_tokens=input_tokens, output_tokens=output_tokens,
        )

    async def health_check(self) -> bool:
        """Check if the provider is healthy."""
        try:
            await self._client.chat.completions.create(
                model="gpt-4o-mini", max_tokens=10, messages=[{"role": "user", "content": "hi"}],
            )
            return True
        except Exception:
            return False
