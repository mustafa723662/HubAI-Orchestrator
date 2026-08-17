import os
from functools import lru_cache

from dotenv import load_dotenv

load_dotenv()


@lru_cache
def get_settings() -> dict[str, str | None]:
    return {
        "gemini_api_key": os.getenv("GEMINI_API_KEY"),
        "gemini_model": os.getenv("GEMINI_MODEL", "gemini-flash-lite-latest"),
    }


def get_gemini_api_key() -> str:
    api_key = get_settings()["gemini_api_key"]
    if not api_key:
        raise ValueError("GEMINI_API_KEY is not set. Add it to backend/.env")
    return api_key


def get_gemini_model() -> str:
    return get_settings()["gemini_model"] or "gemini-flash-lite-latest"


def get_optional_env(name: str) -> str | None:
    """Read an optional env var (e.g. a not-yet-configured provider key)."""
    return os.getenv(name)


def get_jwt_secret_key() -> str:
    key = os.getenv("JWT_SECRET_KEY")
    if not key:
        raise ValueError("JWT_SECRET_KEY is not set. Add it to backend/.env")
    return key


def get_jwt_expire_minutes() -> int:
    return int(os.getenv("JWT_EXPIRE_MINUTES", "10080"))  # 7 days


def get_allowed_origins() -> list[str]:
    """Comma-separated list of allowed frontend origins for CORS.

    Defaults to "*" (dev convenience — matches local file:// / any port
    testing). Set ALLOWED_ORIGINS in production, e.g.
    "https://your-frontend.netlify.app,https://your-frontend.vercel.app".
    """
    raw = os.getenv("ALLOWED_ORIGINS", "*")
    origins = [origin.strip() for origin in raw.split(",") if origin.strip()]
    return origins or ["*"]


def get_database_url() -> str:
    """SQLAlchemy connection string. Defaults to a local SQLite file so
    nothing changes for local dev; set DATABASE_URL in production to point
    at Postgres etc. (e.g. Render's managed Postgres, Neon, Supabase)."""
    return os.getenv("DATABASE_URL", "")


def get_daily_gemini_cap() -> int:
    """Soft cap on total /execute calls per day, shared across all users.

    Protects the Gemini free-tier daily quota (currently 20 req/day per
    model) from being silently exhausted by real traffic — once hit,
    /execute fails fast with a clear message instead of forwarding a raw
    429 from Gemini. Set below your actual Gemini quota with some buffer.
    """
    return int(os.getenv("DAILY_GEMINI_CAP", "18"))
