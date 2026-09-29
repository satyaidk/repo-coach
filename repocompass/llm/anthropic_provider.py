from anthropic import AnthropicError, AsyncAnthropic

from .base import LLMError, LLMProvider


class AnthropicProvider(LLMProvider):
    id = "anthropic"
    label = "Anthropic (Claude)"

    def __init__(self, model: str, api_key: str):
        super().__init__(model)
        self._client = AsyncAnthropic(api_key=api_key, timeout=300)

    async def complete(self, system: str, prompt: str, *, json_mode: bool = False) -> str:
        # No JSON switch needed: the prompt asks for JSON and we parse the reply.
        # Streaming avoids HTTP timeouts on long answers; we just wait for the final message.
        try:
            async with self._client.messages.stream(
                model=self.model,
                max_tokens=16_000,
                system=system,
                messages=[{"role": "user", "content": prompt}],
            ) as stream:
                response = await stream.get_final_message()
        except AnthropicError as exc:
            raise LLMError(f"Anthropic request failed: {exc}") from exc
        return "".join(block.text for block in response.content if block.type == "text")
