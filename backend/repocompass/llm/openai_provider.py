from openai import AsyncOpenAI, OpenAIError

from .base import LLMError, LLMProvider


class OpenAIProvider(LLMProvider):
    id = "openai"
    label = "OpenAI"

    def __init__(self, model: str, api_key: str, base_url: str = ""):
        super().__init__(model)
        # base_url lets this also talk to OpenAI-compatible APIs (OpenRouter, Groq, LM Studio...)
        self._client = AsyncOpenAI(api_key=api_key, base_url=base_url or None, timeout=300)

    async def complete(self, system: str, prompt: str, *, json_mode: bool = False) -> str:
        extra = {"response_format": {"type": "json_object"}} if json_mode else {}
        try:
            response = await self._client.chat.completions.create(
                model=self.model,
                messages=[{"role": "system", "content": system}, {"role": "user", "content": prompt}],
                **extra,
            )
        except OpenAIError as exc:
            raise LLMError(f"OpenAI request failed: {exc}") from exc
        return response.choices[0].message.content or ""
