from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.schemas.route import ExecuteStatus, Provider


class HistoryItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    conversation_id: str
    provider: Provider
    original_prompt: str
    refined_prompt: str
    reasoning: str
    status: ExecuteStatus
    output: str | None
    detail: str | None
    created_at: datetime
