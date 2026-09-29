from google import genai
from google.genai import errors, types

from .base import LLMError, LLMProvider


class GeminiProvider(LLMProvider):
    id = "gemini"
    label = "Google Gemini"

    def __init__(self, model: str, api_key: str):
        super().__init__(model)
        self._client = genai.Client(api_key=api_key)

    async def complete(self, system: str, prompt: str, *, json_mode: bool = False) -> str:
        config = types.GenerateContentConfig(
            system_instruction=system,
            response_mime_type="application/json" if json_mode else None,
        )
        try:
            response = await self._client.aio.models.generate_content(
                model=self.model, contents=prompt, config=config
            )
        except errors.APIError as exc:
            raise LLMError(f"Gemini request failed: {exc}") from exc
        return response.text or ""
