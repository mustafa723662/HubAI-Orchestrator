from fastapi import APIRouter, HTTPException

from app.core.config import get_gemini_api_key, get_gemini_model
from app.schemas.route import ExecuteResponse, RouteRequest
from app.services.gemini_router import route_with_gemini
from app.services.providers import PROVIDER_HANDLERS, ProviderNotConfigured, ProviderUnsupported

router = APIRouter(prefix="/execute", tags=["execute"])


@router.post("", response_model=ExecuteResponse)
async def execute_prompt(payload: RouteRequest) -> ExecuteResponse:
    """Route the prompt with Gemini, then actually call the chosen provider."""
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
    status: str = "ok"

    try:
        output = await handler(decision.refined_prompt)
    except ProviderNotConfigured as exc:
        status = "provider_not_configured"
        detail = str(exc)
    except ProviderUnsupported as exc:
        status = "unsupported_provider"
        detail = str(exc)
    except Exception as exc:
        raise HTTPException(
            status_code=502, detail=f"{decision.provider} call failed: {exc}"
        ) from exc

    return ExecuteResponse(
        provider=decision.provider,
        refined_prompt=decision.refined_prompt,
        reasoning=decision.reasoning,
        original_prompt=payload.prompt,
        status=status,
        output=output,
        detail=detail,
    )
