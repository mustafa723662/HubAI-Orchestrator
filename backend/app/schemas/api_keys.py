from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

# The BYOK-configurable provider names. "openai" also covers DALL-E (same
# API/key). Gemini is system-managed (not user-overridable); Midjourney has
# no API at all.
BYOKProvider = Literal["openai", "claude"]


class ApiKeyUpsertRequest(BaseModel):
    api_key: str = Field(..., min_length=10, max_length=500)


class ApiKeyStatus(BaseModel):
    provider: BYOKProvider
    configured: bool
    masked_key: str | None = None
    updated_at: datetime | None = None
