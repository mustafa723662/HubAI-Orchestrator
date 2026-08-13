import os
from functools import lru_cache

from dotenv import load_dotenv

load_dotenv()


@lru_cache
def get_settings() -> dict[str, str | None]:
    return {
        "gemini_api_key": os.getenv("GEMINI_API_KEY"),
        "gemini_model": os.getenv("GEMINI_MODEL", "gemini-flash-latest"),
    }


def get_gemini_api_key() -> str:
    api_key = get_settings()["gemini_api_key"]
    if not api_key:
        raise ValueError("GEMINI_API_KEY is not set. Add it to backend/.env")
    return api_key


def get_gemini_model() -> str:
    return get_settings()["gemini_model"] or "gemini-flash-latest"


def get_optional_env(name: str) -> str | None:
    """Read an optional env var (e.g. a not-yet-configured provider key)."""
    return os.getenv(name)
