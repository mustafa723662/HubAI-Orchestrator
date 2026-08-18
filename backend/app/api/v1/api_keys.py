from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.core.encryption import decrypt_value, encrypt_value, mask_key
from app.db.database import get_db
from app.db.models import User, UserApiKey
from app.schemas.api_keys import ApiKeyStatus, ApiKeyUpsertRequest, BYOKProvider

router = APIRouter(prefix="/api-keys", tags=["api-keys"])

SUPPORTED_PROVIDERS: list[BYOKProvider] = ["openai", "claude"]


def _get_row(db: Session, user_id: int, provider: str) -> UserApiKey | None:
    return db.scalar(
        select(UserApiKey).where(UserApiKey.user_id == user_id, UserApiKey.provider == provider)
    )


@router.get("", response_model=list[ApiKeyStatus])
def list_api_keys(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[ApiKeyStatus]:
    """Status of the logged-in user's own BYOK keys. Never returns the
    actual key — only whether one is set, a masked preview, and when it was
    last updated."""
    rows = {row.provider: row for row in current_user.api_keys}
    result = []
    for provider in SUPPORTED_PROVIDERS:
        row = rows.get(provider)
        if row is None:
            result.append(ApiKeyStatus(provider=provider, configured=False))
        else:
            # Masked previews aren't stored — decrypting here (GET is
            # infrequent) is simpler than persisting a redundant field.
            plaintext = decrypt_value(row.encrypted_key)
            result.append(
                ApiKeyStatus(
                    provider=provider,
                    configured=True,
                    masked_key=mask_key(plaintext) if plaintext else None,
                    updated_at=row.updated_at,
                )
            )
    return result


@router.put("/{provider}", response_model=ApiKeyStatus)
def upsert_api_key(
    provider: BYOKProvider,
    payload: ApiKeyUpsertRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiKeyStatus:
    """Save (or replace) the logged-in user's own API key for a provider.
    The key is encrypted before it ever touches the database."""
    api_key = payload.api_key.strip()
    if not api_key:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="API anahtarı boş olamaz.")

    encrypted = encrypt_value(api_key)
    row = _get_row(db, current_user.id, provider)
    if row is None:
        row = UserApiKey(user_id=current_user.id, provider=provider, encrypted_key=encrypted)
        db.add(row)
    else:
        row.encrypted_key = encrypted

    db.commit()
    db.refresh(row)

    return ApiKeyStatus(
        provider=provider,
        configured=True,
        masked_key=mask_key(api_key),
        updated_at=row.updated_at,
    )


@router.delete("/{provider}", status_code=status.HTTP_204_NO_CONTENT)
def delete_api_key(
    provider: BYOKProvider,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    """Remove the logged-in user's own key for a provider — /execute will
    fall back to the system key (if configured) or the Gemini fallback."""
    row = _get_row(db, current_user.id, provider)
    if row is not None:
        db.delete(row)
        db.commit()
