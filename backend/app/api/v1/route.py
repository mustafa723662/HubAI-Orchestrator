from fastapi import APIRouter, HTTPException

from app.core.config import get_gemini_api_key, get_gemini_model
from app.schemas.route import RouteRequest, RouteResponse
from app.services.gemini_router import route_with_gemini

router = APIRouter(prefix="/route", tags=["route"])


@router.post("", response_model=RouteResponse)
async def route_prompt(payload: RouteRequest) -> RouteResponse:
    """Analyze the user's prompt with Gemini Flash and return a routing decision."""
    try:
        api_key = get_gemini_api_key()
    except ValueError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    try:
        result = await route_with_gemini(payload.prompt, api_key, get_gemini_model())
    except ValueError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Gemini routing failed: {exc}",
        ) from exc

    return RouteResponse(
        provider=result.provider,
        refined_prompt=result.refined_prompt,
        reasoning=result.reasoning,
        original_prompt=payload.prompt,
    )
