from app.services.providers.base import ProviderUnsupported


async def run_midjourney(
    prompt: str, history: list[dict] | None = None, api_key: str | None = None
) -> str:
    """Midjourney has no official public API — there is no supported way to
    call it programmatically. Third-party/unofficial wrappers exist but rely
    on automating Discord, which violates Midjourney's Terms of Service, so
    this is intentionally left unimplemented."""
    raise ProviderUnsupported(
        "Midjourney has no official API. The router can still recommend it, "
        "but this service cannot call it automatically."
    )
