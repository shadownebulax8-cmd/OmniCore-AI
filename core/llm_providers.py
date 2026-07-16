"""
Swappable LLM provider layer.

CrewAI (via LiteLLM under the hood) accepts a "<provider>/<model>" string
directly on Agent(llm=...) and resolves the matching API key from the
environment. This module is the ONLY place that decides which provider is
active — switch LLM_PROVIDER in .env and every agent picks it up, no other
code changes needed.
"""
import os
from config.settings import settings


def get_llm_string() -> str:
    """
    Returns a LiteLLM-style model string for the currently configured
    provider, and makes sure the matching API key is visible in the
    environment (LiteLLM reads provider keys from os.environ).
    """
    provider = settings.LLM_PROVIDER.lower().strip()

    if provider == "openai":
        if not settings.OPENAI_API_KEY:
            raise RuntimeError(
                "LLM_PROVIDER=openai but OPENAI_API_KEY is empty in .env. "
                "Set it, or switch LLM_PROVIDER=anthropic."
            )
        os.environ["OPENAI_API_KEY"] = settings.OPENAI_API_KEY
        return f"openai/{settings.OPENAI_MODEL}"

    if provider == "anthropic":
        if not settings.ANTHROPIC_API_KEY:
            raise RuntimeError(
                "LLM_PROVIDER=anthropic but ANTHROPIC_API_KEY is empty in .env. "
                "Set it, or switch LLM_PROVIDER=openai."
            )
        os.environ["ANTHROPIC_API_KEY"] = settings.ANTHROPIC_API_KEY
        return f"anthropic/{settings.ANTHROPIC_MODEL}"

    raise ValueError(f"Unknown LLM_PROVIDER '{provider}'. Use 'openai' or 'anthropic'.")
