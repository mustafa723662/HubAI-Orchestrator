from app.core.config import get_optional_env
from app.services.providers.base import ProviderNotConfigured


async def run_dalle(prompt: str, history: list[dict] | None = None) -> str:
    """Generate an image with OpenAI's image models and return its URL.

    `history` is accepted (for a consistent provider interface) but ignored
    — image generation doesn't take conversational context, and the router
    already produces a self-contained `prompt` that resolves any references
    from prior turns.

    Not active yet: requires OPENAI_API_KEY in backend/.env and the
    `openai` package (add `openai>=1.0.0` to requirements.txt, then
    `pip install -r requirements.txt`). Uses the same OpenAI key as the
    text provider.
    """
    api_key = get_optional_env("OPENAI_API_KEY")
    if not api_key:
        raise ProviderNotConfigured(
            "OPENAI_API_KEY is not set. Add it to backend/.env to enable DALL-E image generation."
        )

    try:
        from openai import AsyncOpenAI
    except ImportError as exc:
        raise ProviderNotConfigured(
            "The 'openai' package isn't installed. Add openai>=1.0.0 to "
            "requirements.txt and run `pip install -r requirements.txt`."
        ) from exc

    client = AsyncOpenAI(api_key=api_key)
    model = get_optional_env("OPENAI_IMAGE_MODEL") or "dall-e-3"
    result = await client.images.generate(model=model, prompt=prompt, n=1, size="1024x1024")
    return result.data[0].url or ""
