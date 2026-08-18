import uuid

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_gemini_api_key, get_gemini_model
from app.core.daily_cap import check_and_increment_daily_gemini_cap
from app.core.deps import get_current_user
from app.core.encryption import decrypt_value
from app.core.limiter import limiter
from app.db.database import get_db
from app.db.models import PromptHistory, User, UserApiKey
from app.schemas.route import ExecuteResponse, RouteRequest
from app.services.gemini_router import route_with_gemini
from app.services.providers import PROVIDER_HANDLERS, ProviderNotConfigured, ProviderUnsupported

router = APIRouter(prefix="/execute", tags=["execute"])

# Providers whose output is plain text — safe to substitute with a Gemini
# answer if the chosen provider turns out to be unconfigured, so the user
# still gets a real response instead of a dead end. Image providers (dalle)
# are deliberately excluded: Gemini's text reply is not an image URL, and
# rendering it as one would show a broken image instead of a clean message.
TEXT_FALLBACK_PROVIDERS = {"openai", "claude"}

# Maps a routed provider to the BYOK key a user could have saved for it.
# "dalle" shares OpenAI's key; gemini/midjourney have no BYOK entry (Gemini
# is system-managed, Midjourney has no API at all).
BYOK_LOOKUP = {"openai": "openai", "dalle": "openai", "claude": "claude"}


def _load_conversation_turns(db: Session, user_id: int, conversation_id: str) -> list[dict]:
    """Reconstruct a generic [{role, content}, ...] turn list (oldest first)
    from this user's prior exchanges in the conversation."""
    rows = db.scalars(
        select(PromptHistory)
        .where(
            PromptHistory.user_id == user_id,
            PromptHistory.conversation_id == conversation_id,
        )
        .order_by(PromptHistory.created_at.asc())
    ).all()

    turns: list[dict] = []
    for row in rows:
        turns.append({"role": "user", "content": row.original_prompt})
        if row.output:
            turns.append({"role": "assistant", "content": row.output})
    return turns


def _get_user_provider_key(db: Session, user_id: int, provider: str) -> str | None:
    """The logged-in user's own decrypted BYOK key for `provider`, if they
    have one saved and it decrypts cleanly. None means "use the system key
    (or fall back)" — never raises."""
    byok_provider = BYOK_LOOKUP.get(provider)
    if byok_provider is None:
        return None

    row = db.scalar(
        select(UserApiKey).where(
            UserApiKey.user_id == user_id, UserApiKey.provider == byok_provider
        )
    )
    if row is None:
        return None
    try:
        return decrypt_value(row.encrypted_key)
    except ValueError:
        # API_KEY_ENCRYPTION_KEY missing/misconfigured — degrade to "no
        # user key" rather than crashing the whole /execute request.
        return None


@router.post("", response_model=ExecuteResponse)
@limiter.limit("10/hour")
async def execute_prompt(
    request: Request,
    payload: RouteRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ExecuteResponse:
    """Route the prompt with Gemini, actually call the chosen provider, and
    save the run to the logged-in user's history.

    Pass `conversation_id` (from a previous response) to continue that
    conversation with full prior context; omit it to start a new one.

    If the user has their own API key saved for the routed provider (see
    /api/v1/api-keys), it's used instead of the system key. Otherwise this
    falls back to the system key if configured, and finally to the Gemini
    fallback (see TEXT_FALLBACK_PROVIDERS) if neither exists.
    """
    check_and_increment_daily_gemini_cap()

    conversation_id = payload.conversation_id or uuid.uuid4().hex
    history_turns = (
        _load_conversation_turns(db, current_user.id, conversation_id)
        if payload.conversation_id
        else []
    )

    try:
        gemini_key = get_gemini_api_key()
    except ValueError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    try:
        decision = await route_with_gemini(
            payload.prompt, gemini_key, get_gemini_model(), history_turns
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Gemini routing failed: {exc}") from exc

    handler = PROVIDER_HANDLERS[decision.provider]
    user_provider_key = _get_user_provider_key(db, current_user.id, decision.provider)

    output: str | None = None
    detail: str | None = None
    run_status: str = "ok"

    try:
        output = await handler(decision.refined_prompt, history_turns, user_provider_key)
    except ProviderNotConfigured as exc:
        original_detail = str(exc)
        if decision.provider in TEXT_FALLBACK_PROVIDERS:
            try:
                output = await PROVIDER_HANDLERS["gemini"](decision.refined_prompt, history_turns)
                run_status = "fallback"
                detail = (
                    f"{decision.provider} yapılandırılmadığı için yanıt otomatik olarak "
                    f"Gemini ile üretildi. ({original_detail})"
                )
            except Exception:
                # Gemini fallback itself failed (e.g. transient upstream
                # error) — fall back further to a clean "not configured"
                # message rather than a hard 502.
                run_status = "provider_not_configured"
                detail = original_detail
        else:
            run_status = "provider_not_configured"
            detail = original_detail
    except ProviderUnsupported as exc:
        run_status = "unsupported_provider"
        detail = str(exc)
    except Exception as exc:
        raise HTTPException(
            status_code=502, detail=f"{decision.provider} call failed: {exc}"
        ) from exc

    response = ExecuteResponse(
        provider=decision.provider,
        refined_prompt=decision.refined_prompt,
        reasoning=decision.reasoning,
        original_prompt=payload.prompt,
        status=run_status,
        output=output,
        detail=detail,
        conversation_id=conversation_id,
    )

    db.add(
        PromptHistory(
            user_id=current_user.id,
            conversation_id=conversation_id,
            provider=response.provider,
            original_prompt=response.original_prompt,
            refined_prompt=response.refined_prompt,
            reasoning=response.reasoning,
            status=response.status,
            output=response.output,
            detail=response.detail,
        )
    )
    db.commit()

    return response
