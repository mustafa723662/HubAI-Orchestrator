from google import genai

from app.core.config import get_gemini_api_key, get_gemini_model
from app.services.conversation import to_gemini_contents
from app.services.providers.base import ProviderNotConfigured


async def run_gemini(prompt: str, history: list[dict] | None = None) -> str:
    """Actually run the prompt — optionally with prior conversation history —
    against Gemini and return the text output."""
    try:
        api_key = get_gemini_api_key()
    except ValueError as exc:
        raise ProviderNotConfigured(str(exc)) from exc

    client = genai.Client(api_key=api_key)

    response = await client.aio.models.generate_content(
        model=get_gemini_model(),
        contents=to_gemini_contents(prompt, history),
    )
    return response.text or ""
