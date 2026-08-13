from typing import Literal

from pydantic import BaseModel, Field

Provider = Literal["openai", "claude", "gemini", "midjourney", "dalle"]


class RouteRequest(BaseModel):
    prompt: str = Field(..., min_length=1, description="User prompt to route")


class RouteResponse(BaseModel):
    provider: Provider
    refined_prompt: str
    reasoning: str
    original_prompt: str


ExecuteStatus = Literal["ok", "provider_not_configured", "unsupported_provider"]


class ExecuteResponse(BaseModel):
    provider: Provider
    refined_prompt: str
    reasoning: str
    original_prompt: str
    status: ExecuteStatus
    output: str | None = Field(
        default=None, description="Provider's raw output (text, or an image URL for dalle)."
    )
    detail: str | None = Field(
        default=None, description="Explanation when status isn't 'ok'."
    )
