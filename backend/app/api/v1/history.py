from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.db.database import get_db
from app.db.models import PromptHistory, User
from app.schemas.history import HistoryItem

router = APIRouter(prefix="/history", tags=["history"])

MAX_HISTORY = 5
MAX_SCAN = 200  # safety cap when deduping recent rows into distinct conversations


@router.get("", response_model=list[HistoryItem])
def list_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[PromptHistory]:
    """Last 5 *conversations* for the logged-in user (their most recent turn
    each), newest first — not the last 5 raw turns, so one long chat doesn't
    crowd out everything else in the sidebar."""
    rows = db.scalars(
        select(PromptHistory)
        .where(PromptHistory.user_id == current_user.id)
        .order_by(PromptHistory.created_at.desc())
        .limit(MAX_SCAN)
    ).all()

    seen: set[str] = set()
    latest_per_conversation: list[PromptHistory] = []
    for row in rows:
        if row.conversation_id in seen:
            continue
        seen.add(row.conversation_id)
        latest_per_conversation.append(row)
        if len(latest_per_conversation) >= MAX_HISTORY:
            break

    return latest_per_conversation


@router.get("/{conversation_id}", response_model=list[HistoryItem])
def get_conversation(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[PromptHistory]:
    """Full turn-by-turn thread for one conversation, oldest first — used to
    resume a past conversation from the history sidebar."""
    rows = list(
        db.scalars(
            select(PromptHistory)
            .where(
                PromptHistory.user_id == current_user.id,
                PromptHistory.conversation_id == conversation_id,
            )
            .order_by(PromptHistory.created_at.asc())
        )
    )
    if not rows:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found.")
    return rows


@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
def clear_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    db.execute(delete(PromptHistory).where(PromptHistory.user_id == current_user.id))
    db.commit()
