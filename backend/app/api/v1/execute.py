from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.config import get_gemini_api_key, get_gemini_model
from app.core.deps import get_current_user
from app.db.database import get_db
from app.db.models import PromptHistory, User
from app.schemas.route import ExecuteResponse, RouteRequest
from app.services.gemini_router import route_with_gemini
from app.services.providers import PROVIDER_HANDLERS, ProviderNotConfigured, ProviderUnsupported

router = APIRouter(prefix="/execute", tags=["execute"])


@router.post("", response_model=ExecuteResponse)
async def execute_prompt(
    payload: RouteRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ExecuteResponse:
    """Route the prompt with Gemini, actually call the chosen provider, and
    save the run to the logged-in user's history."""
    try:
        api_key = get_gemini_api_key()
    except ValueError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    try:
        decision = await route_with_gemini(payload.prompt, api_key, get_gemini_model())
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Gemini routing failed: {exc}") from exc

    handler = PROVIDER_HANDLERS[decision.provider]

    output: str | None = None
    detail: str | None = None
    run_status: str = "ok"

    try:
        output = await handler(decision.refined_prompt)
    except ProviderNotConfigured as exc:
        run_status = "provider_not_configured"
        detail = str(exc)
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
    )

    db.add(
        PromptHistory(
            user_id=current_user.id,
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
