from fastapi import APIRouter, Depends, status
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.db.database import get_db
from app.db.models import PromptHistory, User
from app.schemas.history import HistoryItem

router = APIRouter(prefix="/history", tags=["history"])

MAX_HISTORY = 5


@router.get("", response_model=list[HistoryItem])
def list_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[PromptHistory]:
    """Most recent runs for the logged-in user, newest first."""
    return list(
        db.scalars(
            select(PromptHistory)
            .where(PromptHistory.user_id == current_user.id)
            .order_by(PromptHistory.created_at.desc())
            .limit(MAX_HISTORY)
        )
    )


@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
def clear_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    db.execute(delete(PromptHistory).where(PromptHistory.user_id == current_user.id))
    db.commit()
