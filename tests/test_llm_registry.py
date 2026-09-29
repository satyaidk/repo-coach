import asyncio
import dataclasses

import pytest

from repocompass.config import get_settings
from repocompass.llm import LLMError, create_provider, list_providers
from repocompass.llm import registry
from repocompass.llm.ollama_provider import OllamaProvider


def settings(**overrides):
    base = dataclasses.replace(
        get_settings(), openai_api_key="", anthropic_api_key="", gemini_api_key="", ollama_base_url="http://ollama.test"
    )
    return dataclasses.replace(base, **overrides)


def test_unknown_provider():
    with pytest.raises(LLMError, match="Unknown provider"):
        create_provider("skynet", None, settings())


@pytest.mark.parametrize("provider, env_name", [
    ("openai", "OPENAI_API_KEY"), ("anthropic", "ANTHROPIC_API_KEY"), ("gemini", "GEMINI_API_KEY"),
])
def test_cloud_providers_need_a_key(provider, env_name):
    with pytest.raises(LLMError, match=env_name):
        create_provider(provider, None, settings())


@pytest.mark.parametrize("provider, key_field", [
    ("openai", "openai_api_key"), ("anthropic", "anthropic_api_key"), ("gemini", "gemini_api_key"),
])
def test_cloud_providers_use_default_or_chosen_model(provider, key_field):
    configured = settings(**{key_field: "test-key"})
    assert create_provider(provider, None, configured).model == getattr(configured, f"{provider}_model")
    assert create_provider(provider, "  my-model ", configured).model == "my-model"


def test_ollama_needs_no_key_and_budgets_context_from_num_ctx():
    provider = create_provider("ollama", None, settings(ollama_num_ctx=8192))
    assert isinstance(provider, OllamaProvider)
    assert provider.context_chars == (8192 - 4000) * 3
    assert create_provider("ollama", None, settings(ollama_num_ctx=2048)).context_chars == 6000  # floor


def test_list_providers_reports_readiness(monkeypatch):
    async def ollama_down(base_url):
        return None

    monkeypatch.setattr(registry, "list_local_models", ollama_down)
    listed = {p["id"]: p for p in asyncio.run(list_providers(settings(anthropic_api_key="k")))}
    assert listed["anthropic"]["ready"] is True
    assert listed["openai"]["ready"] is False and "API key" in listed["openai"]["note"]
    assert listed["ollama"]["ready"] is False and "ollama serve" in listed["ollama"]["note"]


def test_list_providers_offers_installed_ollama_models(monkeypatch):
    async def ollama_up(base_url):
        return ["qwen3:4b-instruct", "llama3.2:3b"]

    monkeypatch.setattr(registry, "list_local_models", ollama_up)
    listed = {p["id"]: p for p in asyncio.run(list_providers(settings()))}
    assert listed["ollama"]["ready"] is True
    assert listed["ollama"]["models"] == ["qwen3:4b-instruct", "llama3.2:3b"]
