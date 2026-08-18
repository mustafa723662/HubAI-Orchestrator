from typing import Literal

from pydantic import BaseModel, Field

Provider = Literal["openai", "claude", "gemini", "midjourney", "dalle"]


class RouteRequest(BaseModel):
    prompt: str = Field(..., min_length=1, description="User prompt to route")
    conversation_id: str | None = Field(
        default=None,
        description="Continue an existing multi-turn conversation with full context; omit to start a new one.",
    )


class RouteResponse(BaseModel):
    provider: Provider
    refined_prompt: str
    reasoning: str
    original_prompt: str


ExecuteStatus = Literal["ok", "provider_not_configured", "unsupported_provider", "fallback"]


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
        default=None,
        description="Explanation when status isn't 'ok' (also set on 'fallback', explaining the substitution).",
    )
    conversation_id: str = Field(
        description="Pass this back as conversation_id on the next call to continue this chat."
    )
