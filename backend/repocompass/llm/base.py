"""The one interface every AI provider implements, so the rest of the app never cares which is in use."""

from abc import ABC, abstractmethod


class LLMError(Exception):
    """Raised for any provider failure (missing key, network error, bad model name...)."""


class LLMProvider(ABC):
    id: str  # "openai", "anthropic", ...
    label: str  # shown in the UI

    def __init__(self, model: str):
        self.model = model

    @property
    def context_chars(self) -> int:
        """Roughly how many characters of repo context to send. Cloud models take a lot."""
        return 80_000

    @abstractmethod
    async def complete(self, system: str, prompt: str, *, json_mode: bool = False) -> str:
        """Send one system + user message, return the model's text reply."""
