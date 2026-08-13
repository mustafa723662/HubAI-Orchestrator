from app.core.config import get_optional_env
from app.services.providers.base import ProviderNotConfigured


async def run_openai(prompt: str) -> str:
    """Run the refined prompt against OpenAI's chat completions API.

    Not active yet: requires OPENAI_API_KEY in backend/.env and the
    `openai` package (add `openai>=1.0.0` to requirements.txt, then
    `pip install -r requirements.txt`).
    """
    api_key = get_optional_env("OPENAI_API_KEY")
    if not api_key:
        raise ProviderNotConfigured(
            "OPENAI_API_KEY is not set. Add it to backend/.env to enable OpenAI routing."
        )

    try:
        from openai import AsyncOpenAI
    except ImportError as exc:
        raise ProviderNotConfigured(
            "The 'openai' package isn't installed. Add openai>=1.0.0 to "
            "requirements.txt and run `pip install -r requirements.txt`."
        ) from exc

    client = AsyncOpenAI(api_key=api_key)
    model = get_optional_env("OPENAI_MODEL") or "gpt-4o-mini"
    response = await client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.choices[0].message.content or ""
