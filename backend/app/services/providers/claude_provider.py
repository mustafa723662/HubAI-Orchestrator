from app.core.config import get_optional_env
from app.services.conversation import to_chat_messages
from app.services.providers.base import ProviderNotConfigured


async def run_claude(
    prompt: str, history: list[dict] | None = None, api_key: str | None = None
) -> str:
    """Run the prompt — optionally with prior conversation history — against
    Anthropic's Claude API.

    `api_key`, if given, is the caller's own BYOK key (takes priority over
    the system ANTHROPIC_API_KEY). Without either, requires the `anthropic`
    package (add `anthropic>=0.40.0` to requirements.txt, then
    `pip install -r requirements.txt`).
    """
    api_key = api_key or get_optional_env("ANTHROPIC_API_KEY")
    if not api_key:
        raise ProviderNotConfigured(
            "ANTHROPIC_API_KEY is not set. Add it to backend/.env to enable Claude routing."
        )

    try:
        from anthropic import AsyncAnthropic
    except ImportError as exc:
        raise ProviderNotConfigured(
            "The 'anthropic' package isn't installed. Add anthropic>=0.40.0 to "
            "requirements.txt and run `pip install -r requirements.txt`."
        ) from exc

    client = AsyncAnthropic(api_key=api_key)
    model = get_optional_env("ANTHROPIC_MODEL") or "claude-sonnet-4-5"
    response = await client.messages.create(
        model=model,
        max_tokens=2048,
        messages=to_chat_messages(prompt, history),
    )
    return "".join(block.text for block in response.content if block.type == "text")
