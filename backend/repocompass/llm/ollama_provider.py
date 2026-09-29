"""Local models via Ollama's HTTP API (no SDK needed, no API key, nothing leaves your machine)."""

import json

import httpx

from .base import LLMError, LLMProvider

# Streaming means a slow model only has to produce *something* every few minutes,
# instead of finishing the whole answer before a single timeout.
_TIMEOUT = httpx.Timeout(connect=5, read=300, write=60, pool=5)


class OllamaProvider(LLMProvider):
    id = "ollama"
    label = "Ollama (local)"

    def __init__(self, model: str, base_url: str, num_ctx: int):
        super().__init__(model)
        self._base_url = base_url
        self._num_ctx = num_ctx

    @property
    def context_chars(self) -> int:
        # Keep ~4k tokens free for instructions + the answer; ~3 chars per token of code/markdown.
        return max(6_000, (self._num_ctx - 4_000) * 3)

    async def complete(self, system: str, prompt: str, *, json_mode: bool = False) -> str:
        payload = {
            "model": self.model,
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": prompt}],
            "stream": True,
            "options": {"num_ctx": self._num_ctx, "num_predict": 6_000},
        }
        if json_mode:
            payload["format"] = "json"
        parts: list[str] = []
        try:
            async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
                async with client.stream("POST", f"{self._base_url}/api/chat", json=payload) as response:
                    if response.status_code == 404:
                        raise LLMError(
                            f"Ollama model '{self.model}' not found. Pull it with `ollama pull {self.model}`."
                        )
                    if response.status_code >= 400:
                        body = (await response.aread()).decode(errors="replace")
                        raise LLMError(f"Ollama error {response.status_code}: {body[:300]}")
                    async for line in response.aiter_lines():
                        if not line.strip():
                            continue
                        chunk = json.loads(line)
                        if chunk.get("error"):
                            raise LLMError(f"Ollama error: {chunk['error']}")
                        parts.append(chunk.get("message", {}).get("content", ""))
                        if chunk.get("done"):
                            break
        except httpx.ConnectError as exc:
            raise LLMError(
                f"Can't reach Ollama at {self._base_url}. Is it running? Start it with `ollama serve`."
            ) from exc
        except httpx.ReadTimeout as exc:
            raise LLMError(
                f"Ollama stopped responding for 5 minutes while running {self.model}. "
                "Try a smaller OLLAMA_NUM_CTX in .env, or a smaller model."
            ) from exc
        except httpx.HTTPError as exc:
            raise LLMError(f"Ollama request failed: {exc!r}") from exc
        return "".join(parts)


async def list_local_models(base_url: str) -> list[str] | None:
    """Model names installed in Ollama, or None if the server isn't running."""
    try:
        async with httpx.AsyncClient(timeout=2) as client:
            response = await client.get(f"{base_url}/api/tags")
            response.raise_for_status()
    except httpx.HTTPError:
        return None
    return [m["name"] for m in response.json().get("models", [])]
