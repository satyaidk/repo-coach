"""Create a provider by name. This is the single place that knows about all four providers."""

from ..config import Settings
from .base import LLMError, LLMProvider
from .ollama_provider import OllamaProvider, list_local_models

PROVIDERS = {
    "ollama": "Ollama (local)",
    "openai": "OpenAI",
    "anthropic": "Anthropic (Claude)",
    "gemini": "Google Gemini",
}

_SUGGESTED_MODELS = {
    "openai": ["gpt-5-mini", "gpt-5", "gpt-4.1-mini"],
    "anthropic": ["claude-opus-5-5", "claude-sonnet-5-5", "claude-haiku-4-5-20251001"],
    "gemini": ["gemini-2.5-flash", "gemini-2.5-pro"],
}


def _default_model(provider: str, settings: Settings) -> str:
    return {
        "ollama": settings.ollama_model,
        "openai": settings.openai_model,
        "anthropic": settings.anthropic_model,
        "gemini": settings.gemini_model,
    }[provider]


def _api_key(provider: str, settings: Settings) -> str:
    return {
        "openai": settings.openai_api_key,
        "anthropic": settings.anthropic_api_key,
        "gemini": settings.gemini_api_key,
    }.get(provider, "")


def _missing_package(package: str) -> LLMError:
    return LLMError(f"The `{package}` package isn't installed. Run: pip install {package}")


def create_provider(provider: str, model: str | None, settings: Settings) -> LLMProvider:
    if provider not in PROVIDERS:
        raise LLMError(f"Unknown provider '{provider}'. Choose one of: {', '.join(PROVIDERS)}")
    model = (model or "").strip() or _default_model(provider, settings)

    if provider == "ollama":
        return OllamaProvider(model, settings.ollama_base_url, settings.ollama_num_ctx)

    api_key = _api_key(provider, settings)
    if not api_key:
        env_name = {"openai": "OPENAI_API_KEY", "anthropic": "ANTHROPIC_API_KEY", "gemini": "GEMINI_API_KEY"}
        raise LLMError(f"{PROVIDERS[provider]} needs an API key: set {env_name[provider]} in your .env file.")

    # Imported lazily so you only need the SDKs for the providers you actually use.
    if provider == "openai":
        try:
            from .openai_provider import OpenAIProvider
        except ImportError:
            raise _missing_package("openai") from None
        return OpenAIProvider(model, api_key, settings.openai_base_url)
    if provider == "anthropic":
        try:
            from .anthropic_provider import AnthropicProvider
        except ImportError:
            raise _missing_package("anthropic") from None
        return AnthropicProvider(model, api_key)
    try:
        from .gemini_provider import GeminiProvider
    except ImportError:
        raise _missing_package("google-genai") from None
    return GeminiProvider(model, api_key)


async def list_providers(settings: Settings) -> list[dict]:
    """What the UI's provider picker shows: which providers are ready and which models to offer."""
    local_models = await list_local_models(settings.ollama_base_url)
    result = []
    for provider, label in PROVIDERS.items():
        default = _default_model(provider, settings)
        if provider == "ollama":
            ready = local_models is not None
            models = local_models or [default]
            note = "" if ready else "Ollama isn't running. Start it with `ollama serve`."
        else:
            ready = bool(_api_key(provider, settings))
            models = list(dict.fromkeys([default, *_SUGGESTED_MODELS[provider]]))
            note = "" if ready else "No API key in .env"
        result.append(
            {"id": provider, "label": label, "ready": ready, "default_model": default, "models": models, "note": note}
        )
    return result
