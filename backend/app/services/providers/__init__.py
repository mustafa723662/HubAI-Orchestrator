from app.services.providers.base import ProviderNotConfigured, ProviderUnsupported
from app.services.providers.claude_provider import run_claude
from app.services.providers.dalle_provider import run_dalle
from app.services.providers.gemini_provider import run_gemini
from app.services.providers.midjourney_provider import run_midjourney
from app.services.providers.openai_provider import run_openai

# Maps the provider name chosen by the router to the function that actually
# calls that provider. Add a new entry here when a new provider is wired up.
PROVIDER_HANDLERS = {
    "gemini": run_gemini,
    "openai": run_openai,
    "claude": run_claude,
    "dalle": run_dalle,
    "midjourney": run_midjourney,
}

__all__ = [
    "PROVIDER_HANDLERS",
    "ProviderNotConfigured",
    "ProviderUnsupported",
]
